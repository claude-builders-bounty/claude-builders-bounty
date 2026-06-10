#!/usr/bin/env bash
# changelog-generator.sh — 从git历史自动生成结构化的CHANGELOG.md
# 用法: bash changelog-generator.sh [从哪个tag开始]
# 例: bash changelog-generator.sh v1.0.0
set -euo pipefail

# ─── 配置 ─────────────────────────────────────
SINCE_TAG="${1:-}"
OUTPUT="CHANGELOG.md"
DATE=$(date +%Y-%m-%d)

# ─── 检测上次发布的tag ─────────────────────────
if [ -z "$SINCE_TAG" ]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
fi

echo "📋 从 ${SINCE_TAG} 生成 CHANGELOG..."

# ─── 获取提交信息 ──────────────────────────────
COMMITS=$(git log "${SINCE_TAG}..HEAD" --pretty=format:"%s|||%b" --no-merges 2>/dev/null || true)

if [ -z "$COMMITS" ]; then
    echo "ℹ️  自 ${SINCE_TAG} 以来没有新提交"
    exit 0
fi

# ─── 分类提交 ──────────────────────────────────
ADDED=""; FIXED=""; CHANGED=""; REMOVED=""; DOCS=""; OTHER=""

while IFS= read -r line; do
    TITLE="${line%%|||*}"
    BODY="${line#*|||}"
    [ "$TITLE" = "$BODY" ] && BODY=""
    
    LOWERCASE=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]')
    
    if echo "$LOWERCASE" | grep -qE '^(feat|feature|add|implement|create|new)'; then
        ADDED="$ADDED
  - $TITLE"
    elif echo "$LOWERCASE" | grep -qE '^(fix|bug|hotfix|patch|resolve|correct)'; then
        FIXED="$FIXED
  - $TITLE"
    elif echo "$LOWERCASE" | grep -qE '^(change|update|refactor|improve|optimize|migrate|bump)'; then
        CHANGED="$CHANGED
  - $TITLE"
    elif echo "$LOWERCASE" | grep -qE '^(remove|deprecate|delete|drop)'; then
        REMOVED="$REMOVED
  - $TITLE"
    elif echo "$LOWERCASE" | grep -qE '^(docs?|readme|document)'; then
        DOCS="$DOCS
  - $TITLE"
    else
        OTHER="$OTHER
  - $TITLE"
    fi
done <<< "$COMMITS"

# ─── 生成CHANGELOG.md ──────────────────────────
cat > "$OUTPUT" << EOF
# Changelog

## [Unreleased] — ${DATE}

EOF

[ -n "$ADDED" ] && echo "### ✨ Added" >> "$OUTPUT" && echo "$ADDED" >> "$OUTPUT" && echo "" >> "$OUTPUT"
[ -n "$CHANGED" ] && echo "### 🔄 Changed" >> "$OUTPUT" && echo "$CHANGED" >> "$OUTPUT" && echo "" >> "$OUTPUT"
[ -n "$FIXED" ] && echo "### 🐛 Fixed" >> "$OUTPUT" && echo "$FIXED" >> "$OUTPUT" && echo "" >> "$OUTPUT"
[ -n "$REMOVED" ] && echo "### 🗑️ Removed" >> "$OUTPUT" && echo "$REMOVED" >> "$OUTPUT" && echo "" >> "$OUTPUT"
[ -n "$DOCS" ] && echo "### 📚 Documentation" >> "$OUTPUT" && echo "$DOCS" >> "$OUTPUT" && echo "" >> "$OUTPUT"
[ -n "$OTHER" ] && echo "### 🔧 Other" >> "$OUTPUT" && echo "$OTHER" >> "$OUTPUT" && echo "" >> "$OUTPUT"

echo ""
echo "✅ CHANGELOG.md 已生成 → ${OUTPUT}"
echo ""
echo "┌─────────────────────────────────────┐"
echo "│  💰 这个脚本帮您赚到了 $50 ！       │"
echo "└─────────────────────────────────────┘"
