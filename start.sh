#!/usr/bin/env bash
#
# Launcher — delegates to scripts/start.sh.
#
exec "$(cd "$(dirname "$0")" && pwd)/scripts/start.sh" "$@"
