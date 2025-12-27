#!/usr/bin/env python3
"""
Reachz OSC - Virtual Trackpad Receiver for Mac
Receives OSC messages from Open Stage Control and controls cursor/gestures.

Usage:
    python osc_trackpad.py

Requirements:
    pip install python-osc pyautogui pyobjc-framework-Quartz

macOS Permissions:
    System Preferences → Security & Privacy → Privacy → Accessibility
    Add Terminal.app (or your Python environment) to the allowed list
"""

from pythonosc import dispatcher, osc_server
import pyautogui
import argparse
import sys
import math
import threading
import time

# For scroll events
try:
    from Quartz import (
        CGEventCreateScrollWheelEvent,
        CGEventPost,
        kCGScrollEventUnitLine,
        kCGHIDEventTap
    )
    QUARTZ_AVAILABLE = True
except ImportError:
    QUARTZ_AVAILABLE = False
    print("Warning: Quartz not available, scroll will use pyautogui fallback")

# Disable pyautogui's fail-safe
pyautogui.FAILSAFE = False

# Get screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

# Settings (adjustable via OSC)
speed_multiplier = 1.0
curve_type = "linear"

# Button states for hold behavior
left_held = False
right_held = False

def apply_curve(value, curve):
    """Apply acceleration curve to a normalized value (-0.5 to 0.5)."""
    if curve == "linear":
        return value
    elif curve == "quadratic":
        sign = 1 if value >= 0 else -1
        return sign * (abs(value) ** 1.5)
    elif curve == "smooth":
        v = value + 0.5
        v = max(0, min(1, v))
        v = v * v * (3 - 2 * v)
        return v - 0.5
    return value

def handle_speed(address, *args):
    """Handle /speed OSC messages."""
    global speed_multiplier
    if len(args) >= 1:
        speed_multiplier = float(args[0])

def handle_curve(address, *args):
    """Handle /curve OSC messages."""
    global curve_type
    if len(args) >= 1:
        curve_type = str(args[0])
        print(f"Curve: {curve_type}")

def handle_trackpad(address, *args):
    """Handle /trackpad OSC messages for cursor movement."""
    if len(args) >= 2:
        x_norm, y_norm = args[0], args[1]
        y_norm = 1.0 - y_norm  # Invert Y
        
        x_curved = apply_curve(x_norm - 0.5, curve_type) + 0.5
        y_curved = apply_curve(y_norm - 0.5, curve_type) + 0.5
        
        center_x = SCREEN_WIDTH / 2
        center_y = SCREEN_HEIGHT / 2
        x = int(center_x + (x_curved - 0.5) * SCREEN_WIDTH * speed_multiplier)
        y = int(center_y + (y_curved - 0.5) * SCREEN_HEIGHT * speed_multiplier)
        
        x = max(0, min(x, SCREEN_WIDTH - 1))
        y = max(0, min(y, SCREEN_HEIGHT - 1))
        
        pyautogui.moveTo(x, y, _pause=False)

def handle_tap(address, *args):
    """Handle /tap OSC messages for single click."""
    if len(args) >= 1 and args[0] == 1:
        pyautogui.click(_pause=False)

def handle_left(address, *args):
    """Handle /left OSC messages for left mouse button."""
    global left_held
    if len(args) >= 1:
        if args[0] == 1 and not left_held:
            pyautogui.mouseDown(button='left', _pause=False)
            left_held = True
        elif args[0] == 0 and left_held:
            pyautogui.mouseUp(button='left', _pause=False)
            left_held = False

def handle_right(address, *args):
    """Handle /right OSC messages for right mouse button."""
    global right_held
    if len(args) >= 1:
        if args[0] == 1 and not right_held:
            pyautogui.mouseDown(button='right', _pause=False)
            right_held = True
        elif args[0] == 0 and right_held:
            pyautogui.mouseUp(button='right', _pause=False)
            right_held = False

def handle_scroll(address, *args):
    """Handle /scroll OSC messages for scroll wheel."""
    if len(args) >= 1:
        scroll_value = float(args[0])
        if abs(scroll_value) > 0.5:  # Dead zone
            scroll_amount = int(scroll_value)
            if QUARTZ_AVAILABLE:
                # Use Quartz for smoother scrolling
                event = CGEventCreateScrollWheelEvent(
                    None, 
                    kCGScrollEventUnitLine,
                    1,  # Number of axes
                    scroll_amount
                )
                CGEventPost(kCGHIDEventTap, event)
            else:
                pyautogui.scroll(scroll_amount, _pause=False)

# === Multi-touch gesture state ===
touch_points = {}  # Track multiple touch points
last_pinch_distance = None
last_scroll_y = None

def handle_multixy(address, *args):
    """
    Handle /multixy OSC messages for multi-touch gestures.
    Expects: /multixy [x1, y1, x2, y2, ...]
    """
    global last_pinch_distance, last_scroll_y
    
    if len(args) < 4:
        # Single touch or release - reset
        last_pinch_distance = None
        last_scroll_y = None
        return
    
    # Two touch points
    x1, y1, x2, y2 = args[0], args[1], args[2], args[3]
    
    # Invert Y
    y1 = 1.0 - y1
    y2 = 1.0 - y2
    
    # Calculate distance (for pinch)
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    # Calculate center Y (for scroll)
    center_y = (y1 + y2) / 2
    
    # Two-finger scroll detection
    if last_scroll_y is not None:
        delta_y = center_y - last_scroll_y
        if abs(delta_y) > 0.01:
            scroll_amount = int(delta_y * 20)
            if QUARTZ_AVAILABLE:
                event = CGEventCreateScrollWheelEvent(
                    None, kCGScrollEventUnitLine, 1, scroll_amount
                )
                CGEventPost(kCGHIDEventTap, event)
            else:
                pyautogui.scroll(scroll_amount, _pause=False)
    
    last_scroll_y = center_y
    
    # Pinch detection (for zoom)
    if last_pinch_distance is not None:
        pinch_delta = distance - last_pinch_distance
        if abs(pinch_delta) > 0.02:
            # TODO: Implement magnify gesture via CGEvent
            # For now, use keyboard shortcut
            if pinch_delta > 0:
                pyautogui.hotkey('command', '=', _pause=False)  # Zoom in
            else:
                pyautogui.hotkey('command', '-', _pause=False)  # Zoom out
    
    last_pinch_distance = distance

def handle_multixy_tap(address, *args):
    """Handle two-finger tap for right-click."""
    if len(args) >= 1 and args[0] == 1:
        pyautogui.rightClick(_pause=False)
        print("Right-click (two-finger tap)")

def main():
    parser = argparse.ArgumentParser(description="Reachz OSC Trackpad Receiver")
    parser.add_argument("--ip", default="0.0.0.0", help="IP to listen on")
    parser.add_argument("--port", type=int, default=9000, help="Port to listen on")
    args = parser.parse_args()

    disp = dispatcher.Dispatcher()
    
    # Basic trackpad
    disp.map("/trackpad", handle_trackpad)
    disp.map("/tap", handle_tap)
    disp.map("/speed", handle_speed)
    disp.map("/curve", handle_curve)
    
    # Classic trackpad
    disp.map("/left", handle_left)
    disp.map("/right", handle_right)
    disp.map("/scroll", handle_scroll)
    
    # Magic trackpad (multi-touch)
    disp.map("/multixy", handle_multixy)
    disp.map("/multixy/tap", handle_multixy_tap)

    server = osc_server.ThreadingOSCUDPServer((args.ip, args.port), disp)
    
    print("Reachz OSC Trackpad Receiver")
    print(f"  Listening: {args.ip}:{args.port}")
    print(f"  Screen: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print(f"  Quartz scroll: {'Yes' if QUARTZ_AVAILABLE else 'No (fallback)'}")
    print()
    print("Supported addresses:")
    print("  /trackpad x y    - Cursor movement")
    print("  /tap 1           - Left click")
    print("  /left 0|1        - Left button hold")
    print("  /right 0|1       - Right button hold")
    print("  /scroll n        - Scroll wheel")
    print("  /speed n         - Speed multiplier")
    print("  /curve type      - Acceleration curve")
    print("  /multixy x1 y1 x2 y2 - Multi-touch")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
