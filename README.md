# Reachz OSC

**Turn your phone into a virtual trackpad for Mac** using Open Stage Control and Python.

Mount a small phone or tablet above your keyboard — control cursor, scroll, and gestures without lifting your palms from their resting position.

![Concept](docs/concept.jpg)

## Features

| Session                 | Description                                        |
| ----------------------- | -------------------------------------------------- |
| `trackpad.json`         | Basic trackpad: cursor + tap + speed + curves      |
| `classic_trackpad.json` | Retro style: cursor + L/R buttons + scroll wheel   |
| `magic_trackpad.json`   | Multi-touch: two-finger scroll, pinch zoom, rotate |

## Requirements

- **Mac** (tested on macOS Sonoma)
- **[Open Stage Control](https://openstagecontrol.ammd.net/)** v1.29+
- **Python 3.10+** with:
  ```bash
  pip install python-osc pyautogui pyobjc-framework-Quartz
  ```
- **Phone/Tablet** with a web browser

## Quick Start

1. **Start Open Stage Control** with your session directory pointing to this repo
2. **Run the Python receiver:**
   ```bash
   python osc_trackpad.py
   ```
3. **Load a session** in Open Stage Control (Session → Open)
4. **On your phone**, navigate to `http://<your-mac-ip>:8080`
5. **Grant Accessibility permissions** to Terminal (System Settings → Privacy → Accessibility)

## Sessions

### `trackpad.json` — Basic Trackpad

- XY pad for cursor movement
- Speed slider (0.5x - 3x)
- TAP button for clicks
- Curve selector (linear / quadratic / smooth)

### `classic_trackpad.json` — Classic Trackpad

- XY pad for cursor
- Left + Right click buttons
- Scroll wheel (vertical)
- Speed slider

### `magic_trackpad.json` — Magic Trackpad _(WIP)_

- Multi-touch XY pad (2 fingers)
- Two-finger scroll → macOS scroll events
- Pinch → zoom events
- Two-finger tap → right click
- Rotate gesture _(planned)_

## Hardware Setup

I use a monitor-mounted holder (originally for mechanical keyboard accessories) to position a phone above my keyboard. This keeps fingers on the home row while providing mouse/trackpad access.

_Link to mount: [TODO]_

## How It Works

```
Phone Browser (OSC Widget)
        ↓ OSC over WiFi
Open Stage Control Server (Mac :8080)
        ↓ OSC to localhost:9000
Python Receiver (osc_trackpad.py)
        ↓ pyautogui / Quartz
macOS Cursor & Gesture Events
```

## License

MIT

## Contributing

PRs welcome! Especially for:

- Linux/Windows support
- Additional gesture types
- Better acceleration curves
- UI improvements
