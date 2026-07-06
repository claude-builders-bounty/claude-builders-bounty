#!/usr/bin/env bash
# Run CHANGELOG skill tests — bounty #1
set -euo pipefail
cd "$(dirname "$0")"
python test_changelog.py
echo "OK: all changelog tests passed"
