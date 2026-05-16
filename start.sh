#!/usr/bin/env bash
#
# Legacy launcher — delegates to scripts/start.sh.
#
exec "$(cd "$(dirname "$0")" && pwd)/scripts/start.sh" "$@"
