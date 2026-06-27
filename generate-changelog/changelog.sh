#!/usr/bin/env bash
# changelog.sh — 从 git 历史生成结构化 CHANGELOG.md
# 用法: bash changelog.sh [输出文件] [仓库路径]
# 依赖: git

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO="${2:-.}"

# 切换到目标仓库
cd "$REPO"

# 获取最近的 tag，没有则从第一个 commit 开始
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LATEST_TAG" ]; then RANGE="${LATEST_TAG}..HEAD"
else RANGE=$(git rev-list --max-parents=0 HEAD 2>/dev/null | head -1)..HEAD; fi

# 获取 commit 列表: hash|subject
COMMITS=$(git log "$RANGE" --pretty=format:"%h|%s" --no-merges 2>/dev/null || echo "")

if [ -z "$COMMITS" ]; then
    echo "没有找到新的 commit。"
    exit 0
fi

# 分类容器
ADDED=(); FIXED=(); CHANGED=(); REMOVED=(); OTHER=()

while IFS='|' read -r hash subject; do
    # 跳过空行
    [ -z "$subject" ] && continue
    # 转小写匹配前缀
    lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    entry="- ${subject} (\`${hash}\`)"

    case "$lower" in
        feat:*|add:*|added:*|feature:*)   ADDED+=("$entry") ;;
        fix:*|bugfix:*|hotfix:*)          FIXED+=("$entry") ;;
        refactor:*|change:*|changed:*|update:*|updated:*|improve:*|improved:*|perf:*) CHANGED+=("$entry") ;;
        remove:*|removed:*|delete:*|deleted:*) REMOVED+=("$entry") ;;
        *)                                OTHER+=("$entry") ;;
    esac
done <<< "$COMMITS"

# 生成 CHANGELOG
{
    echo "# Changelog"
    echo ""
    if [ -n "$LATEST_TAG" ]; then
        echo "## [${LATEST_TAG}] — $(date +%Y-%m-%d)"
    else
        echo "## [Unreleased] — $(date +%Y-%m-%d)"
    fi
    echo ""

    if [ ${#ADDED[@]} -gt 0 ]; then
        echo "### Added"
        printf '%s\n' "${ADDED[@]}"
        echo ""
    fi
    if [ ${#FIXED[@]} -gt 0 ]; then
        echo "### Fixed"
        printf '%s\n' "${FIXED[@]}"
        echo ""
    fi
    if [ ${#CHANGED[@]} -gt 0 ]; then
        echo "### Changed"
        printf '%s\n' "${CHANGED[@]}"
        echo ""
    fi
    if [ ${#REMOVED[@]} -gt 0 ]; then
        echo "### Removed"
        printf '%s\n' "${REMOVED[@]}"
        echo ""
    fi
    if [ ${#OTHER[@]} -gt 0 ]; then
        echo "### Other"
        printf '%s\n' "${OTHER[@]}"
        echo ""
    fi
} > "$OUTPUT"

echo "✅ CHANGELOG 已生成: $OUTPUT"
echo "   Added: ${#ADDED[@]} | Fixed: ${#FIXED[@]} | Changed: ${#CHANGED[@]} | Removed: ${#REMOVED[@]} | Other: ${#OTHER[@]}"
