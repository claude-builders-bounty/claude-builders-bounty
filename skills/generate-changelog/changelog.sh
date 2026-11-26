#!/usr/bin/env bash
# 薄壳：真正的实现在 changelog.py，避免依赖 bash 里的一堆细节。
set -euo pipefail
cd "$(dirname "$0")"
exec python3 changelog.py "$@"