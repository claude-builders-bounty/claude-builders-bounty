#!/usr/bin/env bash
set -euo pipefail
mkdir -p dist
cp hooks/block_destructive_bash.py dist/block_destructive_bash.py
chmod +x dist/block_destructive_bash.py
