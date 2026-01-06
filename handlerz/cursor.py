"""
Handler: cursor
Cursor movement via trackpad and dual joysticks.

Input:
    /trackpad x y       - Absolute cursor positioning (0-1 normalized)
    /speed n            - Speed multiplier
    /curve type         - Acceleration curve (linear, quadratic, smooth)
    /joy-left x y       - Left joystick (coarse, high gain)
    /joy-right x y      - Right joystick (fine, low gain)
    /joy-left-gain n    - Adjust left stick sensitivity
    /joy-right-gain n   - Adjust right stick sensitivity

Output:
    Cursor movement via pyautogui

Use Cases:
    - Trackpad tab: absolute cursor control
    - Joystick tab: dual coarse/fine velocity control
"""

import math
import threading
import time
import pyautogui

# Get screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

# Settings
_speed_multiplier = 1.0
_curve_type = "linear"

# Joystick state
_joy_left = [0.0, 0.0]
_joy_right = [0.0, 0.0]
_joy_active = False
_joy_thread = None

# Joystick settings
JOY_DEADZONE = 0.1
JOY_COARSE_GAIN = 25
JOY_FINE_GAIN = 5
JOY_EXPONENT = 2
JOY_UPDATE_RATE = 60

# Addresses this handler responds to
ADDRESSES = [
    "/trackpad", "/speed", "/curve",
    "/joy-left", "/joy-right", "/joy-left-gain", "/joy-right-gain"
]


def _apply_curve(value, curve):
    """Apply acceleration curve to a normalized value."""
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


def _process_joystick_input(raw_x, raw_y, deadzone=JOY_DEADZONE):
    """Apply radial deadzone and rescale."""
    magnitude = math.sqrt(raw_x**2 + raw_y**2)
    if magnitude < deadzone:
        return 0.0, 0.0
    normalized_mag = (magnitude - deadzone) / (1.0 - deadzone)
    scale = normalized_mag / magnitude
    return raw_x * scale, raw_y * scale


def _get_velocity(nx, ny, gain, exponent=JOY_EXPONENT):
    """Calculate velocity vector with power curve."""
    vx = math.copysign(abs(nx) ** exponent, nx) * gain
    vy = math.copysign(abs(ny) ** exponent, ny) * gain
    return vx, vy


def _joystick_update_loop():
    """Background thread that updates cursor based on joystick state."""
    global _joy_active
    interval = 1.0 / JOY_UPDATE_RATE
    accum_x, accum_y = 0.0, 0.0
    
    while _joy_active:
        lx, ly = _process_joystick_input(_joy_left[0], _joy_left[1])
        cx, cy = _get_velocity(lx, ly, JOY_COARSE_GAIN)
        
        rx, ry = _process_joystick_input(_joy_right[0], _joy_right[1])
        fx, fy = _get_velocity(rx, ry, JOY_FINE_GAIN)
        
        accum_x += cx + fx
        accum_y += cy + fy
        
        move_x = int(accum_x)
        move_y = int(accum_y)
        
        if move_x != 0 or move_y != 0:
            pyautogui.moveRel(move_x, -move_y, _pause=False)
            accum_x -= move_x
            accum_y -= move_y
        
        time.sleep(interval)


def _start_joystick_thread():
    """Start the joystick update loop if not already running."""
    global _joy_active, _joy_thread
    if not _joy_active:
        _joy_active = True
        _joy_thread = threading.Thread(target=_joystick_update_loop, daemon=True)
        _joy_thread.start()
        print("Joystick mode activated")


# --- Handler functions ---

def handle_trackpad(address, *args):
    """Absolute cursor positioning."""
    global _speed_multiplier, _curve_type
    if len(args) >= 2:
        x_norm, y_norm = args[0], args[1]
        y_norm = 1.0 - y_norm
        
        x_curved = _apply_curve(x_norm - 0.5, _curve_type) + 0.5
        y_curved = _apply_curve(y_norm - 0.5, _curve_type) + 0.5
        
        center_x = SCREEN_WIDTH / 2
        center_y = SCREEN_HEIGHT / 2
        x = int(center_x + (x_curved - 0.5) * SCREEN_WIDTH * _speed_multiplier)
        y = int(center_y + (y_curved - 0.5) * SCREEN_HEIGHT * _speed_multiplier)
        
        x = max(0, min(x, SCREEN_WIDTH - 1))
        y = max(0, min(y, SCREEN_HEIGHT - 1))
        
        pyautogui.moveTo(x, y, _pause=False)


def handle_speed(address, *args):
    """Set speed multiplier."""
    global _speed_multiplier
    if len(args) >= 1:
        _speed_multiplier = float(args[0])


def handle_curve(address, *args):
    """Set acceleration curve."""
    global _curve_type
    if len(args) >= 1:
        _curve_type = str(args[0])
        print(f"Curve: {_curve_type}")


def handle_joy_left(address, *args):
    """Left joystick (coarse)."""
    global _joy_left
    if len(args) >= 2:
        _joy_left = [float(args[0]), float(args[1])]
        _start_joystick_thread()


def handle_joy_right(address, *args):
    """Right joystick (fine)."""
    global _joy_right
    if len(args) >= 2:
        _joy_right = [float(args[0]), float(args[1])]
        _start_joystick_thread()


def handle_joy_left_gain(address, *args):
    """Adjust left joystick sensitivity."""
    global JOY_COARSE_GAIN
    if len(args) >= 1:
        JOY_COARSE_GAIN = float(args[0])
        print(f"Left joystick gain: {JOY_COARSE_GAIN}")


def handle_joy_right_gain(address, *args):
    """Adjust right joystick sensitivity."""
    global JOY_FINE_GAIN
    if len(args) >= 1:
        JOY_FINE_GAIN = float(args[0])
        print(f"Right joystick gain: {JOY_FINE_GAIN}")


def register(dispatcher):
    """Register all handlers with the dispatcher."""
    dispatcher.map("/trackpad", handle_trackpad)
    dispatcher.map("/speed", handle_speed)
    dispatcher.map("/curve", handle_curve)
    dispatcher.map("/joy-left", handle_joy_left)
    dispatcher.map("/joy-right", handle_joy_right)
    dispatcher.map("/joy-left-gain", handle_joy_left_gain)
    dispatcher.map("/joy-right-gain", handle_joy_right_gain)
