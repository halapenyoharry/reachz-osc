"""
Handler: carry
Provides the "Pregnant Cursor" feature - load text into cursor, drop on click.

Input:
    /carry <text>    - Load text into cursor
    /drop            - Paste text + clear
    /drop-keep       - Paste text + keep for reuse
    /carry-status    - Check if carrying

Output:
    Pastes text at cursor location via clipboard + Cmd+V

Use Cases:
    - Voice transcription → paste anywhere
    - Quick text snippets from phone to Mac
    - Carry text across applications
"""

import threading
import subprocess
import pyautogui

# State
_payload = None
_lock = threading.Lock()

# Addresses this handler responds to
ADDRESSES = ["/carry", "/drop", "/drop-keep", "/carry-status"]


def handle_carry(address, *args):
    """Load text into cursor."""
    global _payload
    if len(args) >= 1:
        text = str(args[0])
        with _lock:
            _payload = text
        preview = text[:40] + "..." if len(text) > 40 else text
        print(f"📦 Carrying: '{preview}'")
        # macOS notification
        try:
            subprocess.run([
                "osascript", "-e",
                f'display notification "{preview}" with title "Reachz: Carrying"'
            ], capture_output=True)
        except:
            pass


def handle_drop(address, *args):
    """Paste text and clear."""
    global _payload
    with _lock:
        if _payload is not None:
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            process.communicate(_payload.encode('utf-8'))
            pyautogui.hotkey('command', 'v', _pause=False)
            print(f"📤 Dropped: '{_payload[:30]}...'" if len(_payload) > 30 else f"📤 Dropped: '{_payload}'")
            _payload = None


def handle_drop_keep(address, *args):
    """Paste text but keep payload."""
    with _lock:
        if _payload is not None:
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            process.communicate(_payload.encode('utf-8'))
            pyautogui.hotkey('command', 'v', _pause=False)
            print(f"📤 Dropped (kept): '{_payload[:30]}...'" if len(_payload) > 30 else f"📤 Dropped (kept): '{_payload}'")


def handle_carry_status(address, *args):
    """Check if carrying."""
    with _lock:
        if _payload is not None:
            print(f"📦 Currently carrying: '{_payload[:30]}...'" if len(_payload) > 30 else f"📦 Currently carrying: '{_payload}'")
        else:
            print("📭 Not carrying anything")


def clear_payload():
    """Clear payload (called by escape key handler)."""
    global _payload
    with _lock:
        if _payload is not None:
            print(f"🚫 Carry cancelled (was: '{_payload[:30]}...')" if len(_payload) > 30 else f"🚫 Carry cancelled (was: '{_payload}')")
            _payload = None


def register(dispatcher):
    """Register all handlers with the dispatcher."""
    dispatcher.map("/carry", handle_carry)
    dispatcher.map("/drop", handle_drop)
    dispatcher.map("/drop-keep", handle_drop_keep)
    dispatcher.map("/carry-status", handle_carry_status)
