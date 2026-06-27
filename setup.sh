#!/usr/bin/env bash
set -euo pipefail

# 这个项目只靠 Python 标准库，环境锁定就该保持轻巧。
python3 --version
chmod +x hooks/block_destructive_bash.py install.sh

echo "✅ Environment ready"
echo "Run: make type-check && make test && make lint && make build"
