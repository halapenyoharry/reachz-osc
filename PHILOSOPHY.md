# Reachz Philosophy

## What Reachz Is

**Control-of-anything for anyone with a discarded phone.**

Reachz turns old phones and tablets into control surfaces for your Mac. It's the Apple Touch Bar without the Apple tax or walled garden.

## Core Principles

1. **Free and Open** — Phones under $100 are everywhere. This software is free.

2. **UNIX Philosophy** — Each handler does one thing well. Drop a file in `handlerz/`, it works.

3. **For Humans, Not Monetization** — We build tools that solve real problems, not engagement metrics.

4. **Understand What You Build** — Every component is documented. A beginner should be able to modify it.

## The Flint Scraper

Millions of years ago, a human's nails broke while scraping meat from bones. She picked up a piece of flint and used it instead. Her tribe adopted the technique.

Reachz is a flint scraper — a fundamental tool that anyone can pick up, understand, and improve.

## Structure

```
reachz-osc/
├── reachz.py        # Entry point (thin loader)
├── handlerz/        # Modular handlers (auto-discovered)
│   ├── carry.py     # "Pregnant cursor" text carry/drop
│   ├── click.py     # Mouse buttons
│   ├── cursor.py    # Trackpad + joystick movement
│   └── scroll.py    # Scroll wheel
└── osc-sessions/    # Open Stage Control UI definitions
```

## Contributing

Add a handler:

1. Create `handlerz/yourhandler.py`
2. Define `ADDRESSES` list and `register(dispatcher)` function
3. Document at the top: Input, Output, Use Cases

That's it. Auto-discovery handles the rest.
