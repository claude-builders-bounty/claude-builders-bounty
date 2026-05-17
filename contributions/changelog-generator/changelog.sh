#!/bin/bash
# 🦞 changelog.sh — Structured CHANGELOG generator from git history
# Usage: bash changelog.sh [--tag v1.0.0] [--output CHANGELOG.md]

set -e

TAG=""
OUTPUT="CHANGELOG.md"
REPO_DIR="."

# 解析参数
while [[ $# -gt 0 ]]; do
  case $1 in
    --tag) TAG="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --repo) REPO_DIR="$2"; shift 2 ;;
    *) echo "用法: bash changelog.sh [--tag v1.0.0] [--output CHANGELOG.md] [--repo /path/to/repo]"; exit 1 ;;
  esac
done

cd "$REPO_DIR"

# 检查git
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "❌ 不是git仓库"
  exit 1
fi

# 确定比较范围
if [ -z "$TAG" ]; then
  # 找最近的tag，没有就用第一个commit
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [ -n "$LATEST_TAG" ]; then
    TAG="$LATEST_TAG"
    RANGE="$TAG..HEAD"
  else
    RANGE="HEAD"
  fi
else
  RANGE="$TAG..HEAD"
fi

echo "🔍 生成CHANGELOG (范围: $RANGE)"

# 初始化分类
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

# 获取所有commit
COMMITS=$(git log --no-merges --pretty=format:"%s||%h||%an" "$RANGE" 2>/dev/null)

if [ -z "$COMMITS" ]; then
  echo "⚠️ 没有找到commit"
  echo "# Changelog" > "$OUTPUT"
  echo "" >> "$OUTPUT"
  echo "No changes since last release." >> "$OUTPUT"
  exit 0
fi

# 分类commit（按常规标识 + 关键词）
while IFS= read -r line; do
  msg=$(echo "$line" | cut -d'|' -f1)
  hash=$(echo "$line" | cut -d'|' -f2)
  author=$(echo "$line" | cut -d'|' -f3)
  
  # 转换为小写用于匹配
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
  
  entry="- $msg (#$hash by $author)"
  
  if echo "$lower" | grep -qE '^(feat|add|new|implement|create|引入|新增|添加)'; then
    ADDED="$ADDED\n$entry"
  elif echo "$lower" | grep -qE '^(fix|bug|hotfix|patch|repair|修复|解决|修补)'; then
    FIXED="$FIXED\n$entry"
  elif echo "$lower" | grep -qE '^(remove|delete|deprecate|移除|删除|废弃)'; then
    REMOVED="$REMOVED\n$entry"
  elif echo "$lower" | grep -qE '^(refactor|update|change|improve|optimize|重构|优化|更新|修改)'; then
    CHANGED="$CHANGED\n$entry"
  elif echo "$lower" | grep -qE '^(docs|doc|chore|test|ci|style|perf|文档|测试)'; then
    CHANGED="$CHANGED\n$entry"
  else
    # 无前缀的按关键词猜
    if echo "$lower" | grep -qE 'fix|bug|issue|error|wrong|missing|fail|break'; then
      FIXED="$FIXED\n$entry"
    else
      ADDED="$ADDED\n$entry"
    fi
  fi
done <<< "$COMMITS"

# 生成CHANGELOG.md
CURRENT_DATE=$(date +%Y-%m-%d)
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.1.0")

cat > "$OUTPUT" << EOF
# Changelog

## [${VERSION}] - ${CURRENT_DATE}

EOF

if [ -n "$ADDED" ]; then
  echo "### ✨ Added" >> "$OUTPUT"
  echo -e "$ADDED" | grep -v '^$' >> "$OUTPUT"
  echo "" >> "$OUTPUT"
fi

if [ -n "$FIXED" ]; then
  echo "### 🐛 Fixed" >> "$OUTPUT"
  echo -e "$FIXED" | grep -v '^$' >> "$OUTPUT"
  echo "" >> "$OUTPUT"
fi

if [ -n "$CHANGED" ]; then
  echo "### 🔄 Changed" >> "$OUTPUT"
  echo -e "$CHANGED" | grep -v '^$' >> "$OUTPUT"
  echo "" >> "$OUTPUT"
fi

if [ -n "$REMOVED" ]; then
  echo "### 🗑️ Removed" >> "$OUTPUT"
  echo -e "$REMOVED" | grep -v '^$' >> "$OUTPUT"
  echo "" >> "$OUTPUT"
fi

echo "✅ CHANGELOG 已生成 → $OUTPUT"
