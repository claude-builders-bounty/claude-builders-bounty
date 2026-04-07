#!/bin/bash
# 📜 CHANGELOG Generator - Bash版本
# 自动生成结构化的CHANGELOG.md from git history

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "📜 CHANGELOG Generator"
echo "======================"

# 检查是否在git仓库中
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ 错误：当前目录不是git仓库${NC}"
    echo "请在一个git仓库中运行此脚本"
    exit 1
fi

# 获取最新的tag
LAST_TAG=$(git tag --sort=-creatordate | head -1)

if [ -n "$LAST_TAG" ]; then
    echo "📌 最新tag: $LAST_TAG"
    echo "📋 获取自 $LAST_TAG 以来的commits..."
    COMMIT_RANGE="${LAST_TAG}..HEAD"
else
    echo -e "${YELLOW}⚠️  未找到git tag，获取最近30个commits...${NC}"
    COMMIT_RANGE="-30"
fi

# 获取commits（格式: hash|date|subject）
COMMITS=$(git log $COMMIT_RANGE --format="%H|%ad|%s" --date=short 2>/dev/null || true)

if [ -z "$COMMITS" ]; then
    echo -e "${YELLOW}⚠️  没有找到新的commits${NC}"
    exit 0
fi

# 统计commits数量
COMMIT_COUNT=$(echo "$COMMITS" | wc -l)
echo -e "${GREEN}✅ 找到 $COMMIT_COUNT 个commits${NC}"

# 生成版本号
if [ -n "$LAST_TAG" ]; then
    # 尝试递增patch版本
    if [[ $LAST_TAG =~ ^v?([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
        MAJOR="${BASH_REMATCH[1]}"
        MINOR="${BASH_REMATCH[2]}"
        PATCH="${BASH_REMATCH[3]}"
        NEW_PATCH=$((PATCH + 1))
        VERSION="v${MAJOR}.${MINOR}.${NEW_PATCH}"
    else
        VERSION="${LAST_TAG}-update"
    fi
else
    VERSION="v0.1.0"
fi

# 获取当前日期
DATE=$(date +%Y-%m-%d)

# 创建临时文件
TEMP_FILE=$(mktemp)

# 写入changelog头部
cat > "$TEMP_FILE" << EOF
# Changelog

## [$VERSION] - $DATE

EOF

# 分类commits
ADDED_COMMITS=""
FIXED_COMMITS=""
CHANGED_COMMITS=""
REMOVED_COMMITS=""

# 处理每个commit
while IFS='|' read -r HASH DATE_STR SUBJECT; do
    SHORT_HASH="${HASH:0:7}"
    
    # 分类逻辑
    LOWER_SUBJECT=$(echo "$SUBJECT" | tr '[:upper:]' '[:lower:]')
    
    if echo "$LOWER_SUBJECT" | grep -qE "^(feat|feature|add|new|implement|introduce|create)"; then
        ADDED_COMMITS="${ADDED_COMMITS}- ${SUBJECT} (${SHORT_HASH})\n"
    elif echo "$LOWER_SUBJECT" | grep -qE "^(fix|bugfix|bug|repair|resolve|patch|hotfix)"; then
        FIXED_COMMITS="${FIXED_COMMITS}- ${SUBJECT} (${SHORT_HASH})\n"
    elif echo "$LOWER_SUBJECT" | grep -qE "^(remove|delete|drop|cleanup|deprecate|eliminate)"; then
        REMOVED_COMMITS="${REMOVED_COMMITS}- ${SUBJECT} (${SHORT_HASH})\n"
    else
        CHANGED_COMMITS="${CHANGED_COMMITS}- ${SUBJECT} (${SHORT_HASH})\n"
    fi
done <<< "$COMMITS"

# 写入分类内容
if [ -n "$ADDED_COMMITS" ]; then
    echo "### Added" >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    echo -e "$ADDED_COMMITS" >> "$TEMP_FILE"
fi

if [ -n "$CHANGED_COMMITS" ]; then
    echo "### Changed" >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    echo -e "$CHANGED_COMMITS" >> "$TEMP_FILE"
fi

if [ -n "$FIXED_COMMITS" ]; then
    echo "### Fixed" >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    echo -e "$FIXED_COMMITS" >> "$TEMP_FILE"
fi

if [ -n "$REMOVED_COMMITS" ]; then
    echo "### Removed" >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    echo -e "$REMOVED_COMMITS" >> "$TEMP_FILE"
fi

# 如果CHANGELOG.md已存在，保留旧内容
if [ -f "CHANGELOG.md" ]; then
    # 提取旧内容（从第一个版本开始）
    OLD_CONTENT=$(tail -n +4 CHANGELOG.md 2>/dev/null || true)
    if [ -n "$OLD_CONTENT" ]; then
        echo "" >> "$TEMP_FILE"
        echo "$OLD_CONTENT" >> "$TEMP_FILE"
    fi
fi

# 写入最终文件
mv "$TEMP_FILE" CHANGELOG.md

echo ""
echo -e "${GREEN}✅ CHANGELOG已生成: CHANGELOG.md${NC}"
echo "📄 版本: $VERSION"
echo "📝 包含 $COMMIT_COUNT 个commits"
echo ""
echo "预览:"
echo "------------------------------"
head -30 CHANGELOG.md
