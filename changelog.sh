#!/usr/bin/env bash
# Wrapper script to execute the python-based changelog generator
python3 "$(dirname "$0")/scripts/generate_changelog.py" "$@"
