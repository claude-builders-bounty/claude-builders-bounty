#!/usr/bin/env bash
set -euo pipefail
bash -n scripts/install.sh
python3 -m py_compile hooks/pre_tool_use_blocker.py
