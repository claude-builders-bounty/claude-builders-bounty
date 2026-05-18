#!/bin/bash
# CHANGELOG Generator Wrapper
# Works via: bash changelog.sh or ./changelog.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
python3 "$SCRIPT_DIR/generate_changelog.py"
