#!/bin/bash
# Hermes Token Dashboard launcher
# Default: GUI desktop app
# Use --tui flag for terminal TUI mode
cd "$(dirname "$0")"
source .venv/Scripts/activate
exec python main.py "$@"
