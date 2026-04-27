#!/usr/bin/env bash
# changelog.sh — 从git历史生成结构化的CHANGELOG.md
# 用法: ./changelog.sh [输出文件] [标签范围]
# 示例: ./changelog.sh CHANGELOG.md v1.0.0..HEAD

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
RANGE="${2:-$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD}"

# 确保在git仓库
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "❌ 错误: 当前目录不是git仓库"
  exit 1
fi

detect_category() {
  local msg="$1"
  msg_lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  if echo "$msg_lower" | grep -qE '^(feat|add|new|implement|create)'; then
    echo "Added"
  elif echo "$msg_lower" | grep -qE '^(fix|bug|patch|hotfix|resolve|repair)'; then
    echo "Fixed"
  elif echo "$msg_lower" | grep -qE '^(change|update|refactor|improve|migrate|upgrade|bump)'; then
    echo "Changed"
  elif echo "$msg_lower" | grep -qE '^(remove|deprecate|delete|drop|clean)'; then
    echo "Removed"
  elif echo "$msg_lower" | grep -qE '^(docs|doc|readme)'; then
    echo "Documentation"
  else
    echo "Other"
  fi
}

CATEGORIES=()
declare -A COMMITS_BY_CAT

add_commit() {
  local cat="$1" line="$2"
  if [ -z "${COMMITS_BY_CAT[$cat]+x}" ]; then
    COMMITS_BY_CAT[$cat]=""
    CATEGORIES+=("$cat")
  fi
  COMMITS_BY_CAT[$cat]="${COMMITS_BY_CAT[$cat]}- ${line}
"
}

while IFS='|' read -r hash msg author date; do
  [ -z "$hash" ] && continue
  category=$(detect_category "$msg")
  short_hash="${hash:0:7}"
  line="- **${msg}** ([${short_hash}](https://github.com/$(git remote get-url origin 2>/dev/null | sed 's/.*:\(.*\)\.git/\1/')/commit/${hash})) — ${author}"
  add_commit "$category" "$line"
done < <(git log --reverse --format="%H|%s|%an|%aI" "$RANGE" 2>/dev/null)

{
  echo "# Changelog"
  echo
  echo "> 自动从git历史生成 | 范围: \`$RANGE\`"
  echo

  CAT_ORDER=("Added" "Changed" "Fixed" "Removed" "Documentation" "Other")
  for cat in "${CAT_ORDER[@]}"; do
    commits="${COMMITS_BY_CAT[$cat]}"
    if [ -n "$commits" ]; then
      echo "## $cat"
      echo
      echo -n "$commits"
      echo
    fi
  done

  echo "---"
  echo "_生成时间: $(date '+%Y-%m-%d %H:%M:%S')_"
} > "$OUTPUT"

echo "✅ CHANGELOG已生成到 $OUTPUT (共 ${#CATEGORIES[@]} 个分类)"
echo "   $(echo -n "${COMMITS_BY_CAT[@]}" | wc -l) 条提交记录"
