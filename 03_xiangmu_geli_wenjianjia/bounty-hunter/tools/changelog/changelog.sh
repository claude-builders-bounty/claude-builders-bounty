#!/usr/bin/env bash
#
# changelog.sh — 从 git history 生成结构化 CHANGELOG.md
#
# 用法：
#   bash changelog.sh [OUTPUT_PATH]   # 默认输出到仓库根目录 CHANGELOG.md
#
# 验收标准（claude-builders-bounty/claude-builders-bounty#1）：
#   1. 通过 `bash changelog.sh` 或 /generate-changelog 命令运行
#   2. 抓取自上一个 git tag 以来的提交（无 tag 时从首个提交开始）
#   3. 自动归类为 Added / Fixed / Changed / Removed
#   4. 输出规范格式的 CHANGELOG.md
#   5. 在真实 GitHub 仓库上测试（附样例输出）
#   6. README 3 步或更少完成设置
#
# 设计原则：只读 git，不修改仓库；纯 Bash，无外部依赖；不可变（只输出新文件）。

set -euo pipefail

# ---------------------------------------------------------------------------
# 配置：默认输出到当前工作目录下的 CHANGELOG.md（便于在任意仓库子目录运行）
# ---------------------------------------------------------------------------
OUTPUT="${1:-"$(pwd)/CHANGELOG.md"}"

# ---------------------------------------------------------------------------
# 确定提交范围：自上一个 tag 以来；无 tag 时从首个提交开始
# ---------------------------------------------------------------------------
REPO_ROOT="$(git rev-parse --show-toplevel)"
PREV_TAG="$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$PREV_TAG" ]]; then
  COMMIT_RANGE="$PREV_TAG..HEAD"
else
  # 无 tag：枚举所有可达提交（包含首个提交），按提交时间正序
  COMMIT_RANGE="HEAD"
fi

# ---------------------------------------------------------------------------
# 抓取提交列表（短哈希 | 主题第一行），按时间正序
# ---------------------------------------------------------------------------
COMMITS=()
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  COMMITS+=("$line")
done < <(git log --format='%h|%s' --reverse $COMMIT_RANGE 2>/dev/null || true)

# ---------------------------------------------------------------------------
# 分类：基于提交主题的惯例前缀与关键词（常规提交格式）
# ---------------------------------------------------------------------------
classify() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  # Added：新功能 / 新增
  if [[ $lower =~ ^(feat|feature|add|new|introduce|implement)[:!]? ]] \
     || [[ $lower =~ \b(add|new feature|implement|introduce)\b ]]; then
    printf 'Added'
    return
  fi

  # Removed：移除 / 删除
  if [[ $lower =~ ^(remove|delete|rm|drop)[:!]? ]] \
     || [[ $lower =~ \b(remove|delete|drop|deprecate)\b ]]; then
    printf 'Removed'
    return
  fi

  # Fixed：修复 Bug / 补丁
  if [[ $lower =~ ^(fix|fixes|fixed|bugfix|resolve|resolved|patch)[:!]? ]] \
     || [[ $lower =~ \b(fix|bugfix|resolve|patch)\b ]]; then
    printf 'Fixed'
    return
  fi

  # 其余（chore / docs / refactor / style / test / ci / build / perf / change / update）→ Changed
  printf 'Changed'
}

# ---------------------------------------------------------------------------
# 将提交归类（使用索引数组保存 "hash|subject"，避免关联数组兼容性问题）
# ---------------------------------------------------------------------------
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

for entry in "${COMMITS[@]}"; do
  [[ -z "$entry" ]] && continue
  hash="${entry%%|*}"
  subject="${entry#*|}"
  case "$(classify "$subject")" in
    Added)   ADDED+=("$hash|$subject")   ;;
    Fixed)   FIXED+=("$hash|$subject")   ;;
    Changed) CHANGED+=("$hash|$subject") ;;
    Removed) REMOVED+=("$hash|$subject") ;;
  esac
done

# ---------------------------------------------------------------------------
# 辅助：输出某一类的条目（稳定按哈希排序）
# ---------------------------------------------------------------------------
emit_category() {
  local title="$1"; shift
  local arr=("$@")
  if [[ ${#arr[@]} -eq 0 ]]; then
    return
  fi
  printf '### %s\n\n' "$title"
  # 按哈希排序并逐行输出，保持稳定顺序（不可变）
  printf '%s\n' "${arr[@]}" | sort -t'|' -k1,1 | while IFS='|' read -r h s; do
    [[ -z "$h" ]] && continue
    printf '%s\n' "- $h — $s"
  done
  printf '\n'
}

# ---------------------------------------------------------------------------
# 生成 CHANGELOG.md
# ---------------------------------------------------------------------------
{
  printf '%s\n' '# Changelog'
  printf '%s\n\n' ''
  printf '%s\n' '## [Unreleased]'
  printf '%s\n\n' ''

  emit_category 'Added'   "${ADDED[@]}"
  emit_category 'Fixed'   "${FIXED[@]}"
  emit_category 'Changed' "${CHANGED[@]}"
  emit_category 'Removed' "${REMOVED[@]}"

  if [[ ${#ADDED[@]} -eq 0 && ${#FIXED[@]} -eq 0 \
       && ${#CHANGED[@]} -eq 0 && ${#REMOVED[@]} -eq 0 ]]; then
    printf '%s\n\n' '_自上次发布以来无变更。_'
  fi

  printf '%s\n' '---'
  printf '%s\n' '*由 `changelog.sh` 从 git history 自动生成。*'
} > "$OUTPUT"

printf 'CHANGELOG 已生成: %s\n' "$OUTPUT"
printf '  Added: %d | Fixed: %d | Changed: %d | Removed: %d\n' \
  "${#ADDED[@]}" "${#FIXED[@]}" "${#CHANGED[@]}" "${#REMOVED[@]}"
