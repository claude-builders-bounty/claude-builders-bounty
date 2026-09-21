#!/usr/bin/env bash
set -euo pipefail
python tools/generate_changelog.py "$@"
