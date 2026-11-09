#!/usr/bin/env bash
# #1：固定脚本位置并完整转发参数，调用者无需切换目录或安装依赖。
set -euo pipefail
script_dir="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/changelog.py" "$@"
