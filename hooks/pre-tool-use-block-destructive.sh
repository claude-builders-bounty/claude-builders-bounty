#!/usr/bin/env bash
# Claude Code pre-tool-use hook — blocks destructive bash commands.
# Requires: Python 3.8+
# This is a thin wrapper; all logic lives in the Python script.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/pre-tool-use-block-destructive.py"
