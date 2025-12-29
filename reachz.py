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

# === Dual Joystick State ===
joy_left = [0.0, 0.0]   # Coarse control (high gain)
joy_right = [0.0, 0.0]  # Fine control (low gain)
joy_active = False
joy_thread = None

# Joystick settings
JOY_DEADZONE = 0.1
JOY_COARSE_GAIN = 25  # pixels per update at full deflection
JOY_FINE_GAIN = 5     # pixels per update at full deflection  
JOY_EXPONENT = 2      # Power curve exponent
JOY_UPDATE_RATE = 60  # Hz

def process_joystick_input(raw_x, raw_y, deadzone=JOY_DEADZONE):
    """Apply radial deadzone and rescale."""
    magnitude = math.sqrt(raw_x**2 + raw_y**2)
    if magnitude < deadzone:
        return 0.0, 0.0
    # Rescale magnitude to start from edge of deadzone
    normalized_mag = (magnitude - deadzone) / (1.0 - deadzone)
    scale = normalized_mag / magnitude
    return raw_x * scale, raw_y * scale

def get_velocity(nx, ny, gain, exponent=JOY_EXPONENT):
    """Calculate velocity vector with power curve."""
    # Preserve sign while applying power curve
    vx = math.copysign(abs(nx) ** exponent, nx) * gain
    vy = math.copysign(abs(ny) ** exponent, ny) * gain
    return vx, vy

def joystick_update_loop():
    """Background thread that updates cursor based on joystick state."""
    global joy_active
    interval = 1.0 / JOY_UPDATE_RATE
    
    # Accumulate fractional movement
    accum_x, accum_y = 0.0, 0.0
    
    while joy_active:
        # Process left stick (coarse)
        lx, ly = process_joystick_input(joy_left[0], joy_left[1])
        cx, cy = get_velocity(lx, ly, JOY_COARSE_GAIN)
        
        # Process right stick (fine)
        rx, ry = process_joystick_input(joy_right[0], joy_right[1])
        fx, fy = get_velocity(rx, ry, JOY_FINE_GAIN)
        
        # Combined velocity (accumulate to handle sub-pixel movement)
        accum_x += cx + fx
        accum_y += cy + fy
        
        # Only move whole pixels, keep fractional part for next update
        move_x = int(accum_x)
        move_y = int(accum_y)
        
        if move_x != 0 or move_y != 0:
            # Y is already correct: positive Y in joystick = up on screen
            pyautogui.moveRel(move_x, -move_y, _pause=False)
            accum_x -= move_x
            accum_y -= move_y
        
        time.sleep(interval)

def start_joystick_thread():
    """Start the joystick update loop if not already running."""
    global joy_active, joy_thread
    if not joy_active:
        joy_active = True
        joy_thread = threading.Thread(target=joystick_update_loop, daemon=True)
        joy_thread.start()
        print("Joystick mode activated")

def handle_joy_left(address, *args):
    """Handle /joy-left OSC messages (coarse cursor control)."""
    global joy_left
    if len(args) >= 2:
        joy_left = [float(args[0]), float(args[1])]
        start_joystick_thread()

def handle_joy_right(address, *args):
    """Handle /joy-right OSC messages (fine cursor control)."""
    global joy_right
    if len(args) >= 2:
        joy_right = [float(args[0]), float(args[1])]
        start_joystick_thread()

def handle_joy_left_gain(address, *args):
    """Handle /joy-left-gain OSC messages (coarse sensitivity)."""
    global JOY_COARSE_GAIN
    if len(args) >= 1:
        JOY_COARSE_GAIN = float(args[0])
        print(f"Left joystick gain: {JOY_COARSE_GAIN}")

def handle_joy_right_gain(address, *args):
    """Handle /joy-right-gain OSC messages (fine sensitivity)."""
    global JOY_FINE_GAIN
    if len(args) >= 1:
        JOY_FINE_GAIN = float(args[0])
        print(f"Right joystick gain: {JOY_FINE_GAIN}")

def handle_scroll_wheel(address, *args):
    """Handle /scroll-wheel encoder (continuous scroll)."""
    if len(args) >= 1:
        scroll_amount = int(args[0])
        if QUARTZ_AVAILABLE:
            event = CGEventCreateScrollWheelEvent(
                None, kCGScrollEventUnitLine, 1, scroll_amount
            )
            CGEventPost(kCGHIDEventTap, event)
        else:
            pyautogui.scroll(scroll_amount, _pause=False)

def handle_scroll_pos(address, *args):
    """Handle /scroll-pos knob (page position indicator - visual only for now)."""
    # This could be used to jump to a specific scroll position
    # For now, just acknowledge receipt
    pass

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
    
    # Dual joystick (coarse/fine)
    disp.map("/joy-left", handle_joy_left)
    disp.map("/joy-right", handle_joy_right)
    disp.map("/joy-left-gain", handle_joy_left_gain)
    disp.map("/joy-right-gain", handle_joy_right_gain)
    disp.map("/scroll-wheel", handle_scroll_wheel)
    disp.map("/scroll-pos", handle_scroll_pos)
    
    # Magic trackpad (multi-touch)
    disp.map("/multixy", handle_multixy)
    disp.map("/multixy/tap", handle_multixy_tap)

    server = osc_server.ThreadingOSCUDPServer((args.ip, args.port), disp)
    
    print("Reachz OSC Trackpad Receiver")
    print(f"  Listening: {args.ip}:{args.port}")
    print(f"  Screen: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print(f"  Quartz scroll: {'Yes' if QUARTZ_AVAILABLE else 'No (fallback)'}")
    print()
    print("Joystick Tab:")
    print("  /joy-left x y        - Coarse cursor (left stick)")
    print("  /joy-right x y       - Fine cursor (right stick)")
    print("  /joy-left-gain n     - Left stick sensitivity")
    print("  /joy-right-gain n    - Right stick sensitivity")
    print("  /scroll-wheel n      - Scroll (encoder)")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
