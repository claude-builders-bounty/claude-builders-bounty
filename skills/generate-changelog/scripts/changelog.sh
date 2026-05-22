#!/bin/bash
# Wrapper for the Python changelog generator
python3 "$(dirname "$0")/generate_changelog.py" "$@"
