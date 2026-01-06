"""
Handler: click
Mouse button handlers for tap, left-click, and right-click.

Input:
    /tap         - Single left click (on value=1)
    /left 0|1    - Left button hold (1=down, 0=up)
    /right 0|1   - Right button hold (1=down, 0=up)

Output:
    Mouse button events via pyautogui

Use Cases:
    - Tap to click from trackpad
    - Hold buttons for drag operations
    - Right-click context menus
"""

import pyautogui

# State
_left_held = False
_right_held = False

# Addresses this handler responds to
ADDRESSES = ["/tap", "/left", "/right"]


def handle_tap(address, *args):
    """Single left click."""
    if len(args) >= 1 and args[0] == 1:
        pyautogui.click(_pause=False)


def handle_left(address, *args):
    """Left mouse button hold."""
    global _left_held
    if len(args) >= 1:
        if args[0] == 1 and not _left_held:
            pyautogui.mouseDown(button='left', _pause=False)
            _left_held = True
        elif args[0] == 0 and _left_held:
            pyautogui.mouseUp(button='left', _pause=False)
            _left_held = False


def handle_right(address, *args):
    """Right mouse button hold."""
    global _right_held
    if len(args) >= 1:
        if args[0] == 1 and not _right_held:
            pyautogui.mouseDown(button='right', _pause=False)
            _right_held = True
        elif args[0] == 0 and _right_held:
            pyautogui.mouseUp(button='right', _pause=False)
            _right_held = False


def register(dispatcher):
    """Register all handlers with the dispatcher."""
    dispatcher.map("/tap", handle_tap)
    dispatcher.map("/left", handle_left)
    dispatcher.map("/right", handle_right)
