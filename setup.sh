#!/usr/bin/env bash
set -euo pipefail

echo "🔍 检查环境..."
python3 --version
bash --version | head -1

echo "📦 无外部依赖，跳过安装"
echo "✅ 环境准备完成"
