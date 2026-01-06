"""
Handler: scroll
Scroll wheel handlers using Quartz for smooth scrolling.

Input:
    /scroll n        - Scroll by n lines (positive=up, negative=down)
    /scroll-wheel n  - Encoder-style scroll

Output:
    Scroll events via Quartz (or pyautogui fallback)

Use Cases:
    - Two-finger scroll simulation
    - Scroll wheel on joystick tab
    - Page navigation
"""

import pyautogui

# Try to import Quartz for native scroll
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

# Addresses this handler responds to
ADDRESSES = ["/scroll", "/scroll-wheel", "/scroll-pos"]


def _do_scroll(amount):
    """Perform scroll with Quartz or fallback."""
    if QUARTZ_AVAILABLE:
        event = CGEventCreateScrollWheelEvent(
            None, kCGScrollEventUnitLine, 1, int(amount)
        )
        CGEventPost(kCGHIDEventTap, event)
    else:
        pyautogui.scroll(int(amount), _pause=False)


def handle_scroll(address, *args):
    """Scroll by amount (with dead zone)."""
    if len(args) >= 1:
        scroll_value = float(args[0])
        if abs(scroll_value) > 0.5:
            _do_scroll(scroll_value)


def handle_scroll_wheel(address, *args):
    """Encoder-style scroll (direct value)."""
    if len(args) >= 1:
        _do_scroll(args[0])


def handle_scroll_pos(address, *args):
    """Scroll position indicator (visual only for now)."""
    pass


def register(dispatcher):
    """Register all handlers with the dispatcher."""
    dispatcher.map("/scroll", handle_scroll)
    dispatcher.map("/scroll-wheel", handle_scroll_wheel)
    dispatcher.map("/scroll-pos", handle_scroll_pos)
