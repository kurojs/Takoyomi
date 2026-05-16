#!/usr/bin/env bash
#
# start.sh — Launch n1-translator headless (no terminal attached).
#
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"
VENV_PYTHON="$DIR/.venv/bin/python"

if [ ! -d "$DIR/.venv" ]; then
    echo "[n1] Creating virtual environment…"
    python3 -m venv "$DIR/.venv"
fi

if ! "$VENV_PYTHON" -c "import PySide6" 2>/dev/null; then
    echo "[n1] Installing dependencies…"
    "$VENV_PYTHON" -m pip install --quiet --upgrade pip
    "$VENV_PYTHON" -m pip install --quiet -r "$DIR/requirements.txt"
fi

# Editable install so ``python -m n1_translator`` works from src/ layout
if ! "$VENV_PYTHON" -c "import n1_translator" 2>/dev/null; then
    "$VENV_PYTHON" -m pip install --quiet -e "$DIR"
fi

echo "[n1] Launching n1-translator…"

# Use the venv python directly — no sourcing needed
nohup "$VENV_PYTHON" -m n1_translator < /dev/null > /tmp/n1.log 2>&1 &
disown

echo "[n1] PID $! — log at /tmp/n1.log"
