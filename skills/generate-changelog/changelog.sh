#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [version]

set -euo pipefail

VERSION="${1:-}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
CHANGELOG_FILE="$REPO_ROOT/CHANGELOG.md"
TODAY=$(date +%Y-%m-%d)

# 获取最新的git tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# 确定版本号
if [ -z "$VERSION" ]; then
  if [ -f "$REPO_ROOT/package.json" ]; then
    VERSION=$(node -e "console.log(require('./package.json').version)" 2>/dev/null || echo "Unreleased")
  else
    VERSION="Unreleased"
  fi
fi

# 收集commits
if [ -n "$LAST_TAG" ]; then
  COMMITS=$(git log "$LAST_TAG..HEAD" --pretty=format:"%s" --no-merges 2>/dev/null || echo "")
else
  COMMITS=$(git log --pretty=format:"%s" --no-merges 2>/dev/null || echo "")
fi

if [ -z "$COMMITS" ]; then
  echo "No new commits found since last tag ($LAST_TAG)."
  exit 0
fi

# 分类
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r commit; do
  [ -z "$commit" ] && continue

  # 提取前缀和描述
  PREFIX=$(echo "$commit" | sed -E 's/^([a-z]+)(\(.+\))?:.*/\1/' | tr '[:upper:]' '[:lower:]')
  DESC=$(echo "$commit" | sed -E 's/^[a-z]+(\(.+\))?:[[:space:]]*//' | sed 's/^./\U&/')

  case "$PREFIX" in
    feat|feature)
      ADDED="$ADDED\n- $DESC"
      ;;
    fix|bugfix)
      FIXED="$FIXED\n- $DESC"
      ;;
    remove|revert|deprecate)
      REMOVED="$REMOVED\n- $DESC"
      ;;
    refactor|perf|chore|build|ci)
      CHANGED="$CHANGED\n- $DESC"
      ;;
    docs|test|style)
      # 跳过
      ;;
    *)
      CHANGED="$CHANGED\n- $DESC"
      ;;
  esac
done <<< "$COMMITS"

# 构建changelog条目
ENTRY="## [$VERSION] - $TODAY"

[ -n "$ADDED" ] && ENTRY="$ENTRY\n\n### Added$ADDED"
[ -n "$FIXED" ] && ENTRY="$ENTRY\n\n### Fixed$FIXED"
[ -n "$CHANGED" ] && ENTRY="$ENTRY\n\n### Changed$CHANGED"
[ -n "$REMOVED" ] && ENTRY="$ENTRY\n\n### Removed$REMOVED"

# 写入CHANGELOG.md
if [ -f "$CHANGELOG_FILE" ]; then
  # 在文件开头插入新条目（跳过可能的标题行）
  EXISTING=$(cat "$CHANGELOG_FILE")
  echo -e "$ENTRY\n\n$EXISTING" > "$CHANGELOG_FILE"
else
  echo -e "# Changelog\n\n$ENTRY" > "$CHANGELOG_FILE"
fi

echo "CHANGELOG.md updated with version $VERSION"
echo -e "$ENTRY"
