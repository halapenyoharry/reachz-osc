#!/usr/bin/env python3
"""
Reachz - Universal OSC Control Interface for Mac

Turn any phone/tablet into a control surface for your Mac.
Receives OSC messages and translates them to cursor, keyboard, and system actions.

Usage:
    python reachz.py

Requirements:
    pip install python-osc pyautogui pyobjc-framework-Quartz pynput

macOS Permissions:
    System Settings → Privacy & Security → Accessibility
    Add Python to the allowed list
"""

from pythonosc import dispatcher, osc_server
import argparse
import sys

# Import the handlerz auto-discovery
from handlerz import register_all

# Optional: keyboard listener for Escape to cancel carry
try:
    from pynput import keyboard as pynput_keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("Warning: pynput not available, Escape key won't cancel carry")


def start_keyboard_listener():
    """Start listening for Escape key to cancel carry."""
    if PYNPUT_AVAILABLE:
        from handlerz import carry
        
        def on_key_press(key):
            try:
                if key == pynput_keyboard.Key.esc:
                    carry.clear_payload()
            except:
                pass
        
        listener = pynput_keyboard.Listener(on_press=on_key_press)
        listener.daemon = True
        listener.start()
        print("  Escape key listener: active")


def main():
    parser = argparse.ArgumentParser(description="Reachz OSC Receiver")
    parser.add_argument("--ip", default="0.0.0.0", help="IP to listen on")
    parser.add_argument("--port", type=int, default=9000, help="Port to listen on")
    args = parser.parse_args()

    disp = dispatcher.Dispatcher()
    
    print("Reachz OSC Receiver")
    print(f"  Listening: {args.ip}:{args.port}")
    print()
    print("Loading handlerz:")
    
    # Auto-discover and register all handlers
    addresses = register_all(disp)
    
    # Start keyboard listener
    start_keyboard_listener()
    
    print()
    print(f"Ready! {len(addresses)} addresses registered.")
    print()

    server = osc_server.ThreadingOSCUDPServer((args.ip, args.port), disp)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
