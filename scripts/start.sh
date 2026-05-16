#!/usr/bin/env bash
#
# start.sh — Launch n1-translator headless (no terminal attached).
#
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"

if [ ! -d .venv ]; then
    echo "[n1] Creating virtual environment…"
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if ! python3 -c "import PySide6" 2>/dev/null; then
    echo "[n1] Installing dependencies…"
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
fi

echo "[n1] Launching n1-translator…"

# Run detached so the terminal can be closed
nohup python3 -m n1_translator < /dev/null > /tmp/n1.log 2>&1 &
disown

echo "[n1] PID $! — log at /tmp/n1.log"
