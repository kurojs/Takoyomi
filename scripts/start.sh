#!/usr/bin/env bash
#
# start.sh — Launch Takoyomi headless (no terminal attached).
#
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"
VENV_PYTHON="$DIR/.venv/bin/python"

if [ ! -d "$DIR/.venv" ]; then
    echo "[takoyomi] Creating virtual environment…"
    python3 -m venv "$DIR/.venv"
fi

if ! "$VENV_PYTHON" -c "import PySide6" 2>/dev/null; then
    echo "[takoyomi] Installing dependencies…"
    "$VENV_PYTHON" -m pip install --quiet --upgrade pip
    "$VENV_PYTHON" -m pip install --quiet -r "$DIR/requirements.txt"
fi

if ! "$VENV_PYTHON" -c "import takoyomi" 2>/dev/null; then
    "$VENV_PYTHON" -m pip install --quiet -e "$DIR"
fi

echo "[takoyomi] Launching Takoyomi…"

nohup "$VENV_PYTHON" -m takoyomi < /dev/null > /tmp/takoyomi.log 2>&1 &
disown

echo "[takoyomi] PID $! — log at /tmp/takoyomi.log"
