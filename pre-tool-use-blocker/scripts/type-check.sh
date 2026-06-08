#!/usr/bin/env bash
set -euo pipefail
python3 -m py_compile hooks/pre_tool_use_blocker.py tests/test_pre_tool_use_blocker.py
