#!/usr/bin/env bash
# Backward-compatible launcher for the stdlib Python implementation.
exec python3 "$(cd -- "$(dirname -- "$0")" && pwd)/block-destructive-bash.py" "$@"
