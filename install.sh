#!/usr/bin/env bash

# Run python installer
if command -v python3 &>/dev/null; then
    python3 "$(dirname "$0")/install.py"
elif command -v python &>/dev/null; then
    python "$(dirname "$0")/install.py"
else
    echo "Error: Python is required to install the hook."
    exit 1
fi
