#!/usr/bin/env bash
set -euo pipefail
python3 -m py_compile hooks/block_destructive_bash.py tests/test_block_destructive_bash.py
