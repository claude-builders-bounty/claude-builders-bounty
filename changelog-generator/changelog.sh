#!/usr/bin/env bash
# CHANGELOG generator — wrapper script
# Usage: ./changelog.sh [--since TAG] [--stdout]
set -euo pipefail

SCRIPT_DIR=""
python3 "/generate_changelog.py" ""
