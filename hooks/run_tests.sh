#!/usr/bin/env bash
# Run all hook acceptance tests — bounty #3
set -euo pipefail
cd "$(dirname "$0")"
python test_hook.py
echo "OK: all hook tests passed"
