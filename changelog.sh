#!/usr/bin/env bash
# Entrypoint for CHANGELOG generator
set -e
python3 "$(dirname "$0")/changelog.py" || python "$(dirname "$0")/changelog.py"
