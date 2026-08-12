#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
    python3 "$SCRIPT_DIR/changelog.py" "$@"
elif command -v python >/dev/null 2>&1; then
    python "$SCRIPT_DIR/changelog.py" "$@"
else
    echo "ERROR: Python no está instalado o no está disponible en PATH."
    exit 1
fi