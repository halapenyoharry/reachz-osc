# Research: Dual-Joystick Cursor Control Logic

## Overview

This document outlines the algorithmic framework for mapping two analog joystick inputs to a single cursor output. The primary objective is to maximize precision through a "Coarse/Fine" control architecture.

---

## 1. Mathematical Framework

The system uses a **Non-Linear Velocity Scaling** model. Unlike direct coordinate mapping, this uses the joystick's displacement to influence the cursor's velocity vector.

### The Transfer Function

The core movement is governed by a power-curve function to allow for granular control near the stick's center while maintaining rapid movement at the outer edge:

$$V = k \cdot (d^n)$$

- **$V$**: Resulting cursor velocity.
- **$k$**: Sensitivity constant (Gain).
- **$d$**: Normalized displacement (0.0 to 1.0).
- **$n$**: Sensitivity exponent (typically $n=3$ to preserve sign and create a "logarithmic feel").

### Dual-Input Summation

To integrate two joysticks (e.g., Left Stick for Coarse, Right Stick for Fine), we apply a weighted sum of their independent velocity vectors:

$$V_{total} = (k_{coarse} \cdot d_{L}^n) + (k_{fine} \cdot d_{R}^m)$$

---

## 2. Implementation Logic (Pseudo-code)

### Step 1: Input Normalization & Deadzone

Analog sticks often suffer from hardware "drift." A radial deadzone must be applied before calculation.

```python
def process_input(raw_x, raw_y, deadzone=0.1):
    magnitude = math.sqrt(raw_x**2 + raw_y**2)
    if magnitude < deadzone:
        return 0, 0
    # Rescale magnitude to start from the edge of the deadzone
    normalized_mag = (magnitude - deadzone) / (1.0 - deadzone)
    scale = normalized_mag / magnitude
    return raw_x * scale, raw_y * scale

```

### Step 2: Velocity Calculation

Applying the power curve and gain constants.

```python
def get_velocity_vector(nx, ny, gain, exponent=3):
    vx = (nx ** exponent) * gain
    vy = (ny ** exponent) * gain
    return vx, vy

```

### Step 3: Global Integration

The final cursor update loop.

```python
while active:
    lx, ly = read_left_stick()   # Range -1 to 1
    rx, ry = read_right_stick()  # Range -1 to 1

    # Process Coarse (High Gain)
    cx, cy = get_velocity_vector(*process_input(lx, ly), gain=25)

    # Process Fine (Low Gain)
    fx, fy = get_velocity_vector(*process_input(rx, ry), gain=5)

    # Update Cursor Position
    cursor.move_relative(x = cx + fx, y = cy + fy)

```

---

## 3. Reference Standards

- **Transfer Functions:** Used in [Libinput](https://wayland.freedesktop.org/libinput/doc/latest/absolute-axes.html) for pointer acceleration.
- **Hardware Precedents:** [US Patent 5914703A](https://patents.google.com/patent/US5914703A/en) (Dual cursor controllers).
- **Accessibility Implementations:** [Joystick-To-Mouse](https://www.imgpresents.com/joy2mse/j2m.htm) (standardized the use of joystick velocity for UI navigation).

```

Would you like me to research the specific **C++ header files** for any open-source joystick drivers that handle this at the kernel level?

```
