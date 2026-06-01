#!/usr/bin/env bash

# Check if Python is installed
if ! command -v python3 &>/dev/null; then
    if ! command -v python &>/dev/null; then
        echo "Error: Python is required to run the changelog generator."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Run the python script in the local directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
$PYTHON_CMD "$SCRIPT_DIR/changelog.py"
