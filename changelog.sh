#!/bin/bash
# 🦞 Changelog Generator - Claude Code SKILL
# Bounty: $50
# 
# 从git历史自动生成结构化 CHANGELOG.md
#
# 用法:
#   chmod +x changelog.sh
#   ./changelog.sh              # 生成完整 CHANGELOG.md
#   ./changelog.sh --since v1.0.0  # 从指定tag开始
#
# 输出: CHANGELOG.md

set -euo pipefail

VERSION="1.0.0"
DATE=$(date +%Y-%m-%d)

# ====== 解析参数 ======
SINCE_TAG=""
OUTPUT_FILE="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
  case $1 in
    --since) SINCE_TAG="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    --help|-h)
      echo "用法: ./changelog.sh [--since <tag>] [--output <file>]"
      echo "  --since <tag>  从指定tag开始 (默认: 最近tag)"
      echo "  --output <file> 输出文件 (默认: CHANGELOG.md)"
      exit 0 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

# ====== 检测git仓库 ======
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "❌ 错误: 当前目录不是git仓库"
  exit 1
fi

REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")

# ====== 确定tag范围 ======
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -n "$SINCE_TAG" ]]; then
  echo "📋 生成变更日志 (自 $SINCE_TAG 以来)"
  RANGE="${SINCE_TAG}..HEAD"
else
  echo "📋 生成完整变更日志"
  RANGE="HEAD"
fi

# ====== 获取分类提交 ======
get_commits() {
  local pattern="$1"
  if [[ -n "$SINCE_TAG" ]]; then
    git log "$RANGE" --pretty=format:"%s" --grep="$pattern" 2>/dev/null || true
  else
    git log --pretty=format:"%s" --grep="$pattern" 2>/dev/null || true
  fi
}

extract_messages() {
  local prefix="$1"
  while IFS= read -r line; do
    if [[ -n "$line" ]]; then
      # 提取commit消息中的具体内容
      local msg=$(echo "$line" | sed -E "s/^${prefix}//I" | sed -E "s/^\([^)]*\)//" | xargs)
      if [[ -n "$msg" ]]; then
        echo "  - $msg"
      fi
    fi
  done
}

# ====== 统计 ======
get_commit_count() {
  if [[ -n "$SINCE_TAG" ]]; then
    git log "$RANGE" --oneline 2>/dev/null | wc -l | tr -d ' '
  else
    git log --oneline 2>/dev/null | wc -l | tr -d ' '
  fi
}

COUNT=$(get_commit_count)
echo "  共 ${COUNT} 次提交"

# ====== 生成CHANGELOG ======
{
  echo "# Changelog"
  echo ""
  echo "## [$VERSION] - $DATE"
  echo ""

  # Added (feat, add, implement, create)
  ADDED=$(git log "$RANGE" --pretty=format:"- %s" --grep="^feat" 2>/dev/null; \
          git log "$RANGE" --pretty=format:"- %s" --grep="^add" 2>/dev/null; \
          git log "$RANGE" --pretty=format:"- %s" --grep="^implement" 2>/dev/null; \
          git log "$RANGE" --pretty=format:"- %s" --grep="^create" 2>/dev/null)
  if [[ -n "$ADDED" ]]; then
    echo "### Added"
    echo "$ADDED" | while IFS= read -r line; do
      # 移除前缀关键词，保留描述
      line=$(echo "$line" | sed -E 's/^- (feat|add|implement|create)\(?[^)]*\)?[:\s]*/- /I' | sed 's/\.$//')
      [[ -n "$(echo "$line" | tr -d ' ') ]] && echo "$line"
    done | sort -u
    echo ""
  fi

  # Fixed (fix, bugfix, hotfix, patch)
  FIXED=$(git log "$RANGE" --pretty=format:"- %s" --grep="^fix" 2>/dev/null; \
          git log "$RANGE" --pretty=format:"- %s" --grep="^bug" 2>/dev/null; \
          git log "$RANGE" --pretty=format:"- %s" --grep="^hotfix" 2>/dev/null; \
          git log "$RANGE" --pretty=format:"- %s" --grep="^patch" 2>/dev/null; \
          git log "$RANGE" --pretty=format:"- %s" --grep="^resolve" 2>/dev/null)
  if [[ -n "$FIXED" ]]; then
    echo "### Fixed"
    echo "$FIXED" | while IFS= read -r line; do
      line=$(echo "$line" | sed -E 's/^- (fix|bugfix|hotfix|patch|resolve)\(?[^)]*\)?[:\s]*/- /I' | sed 's/\.$//')
      [[ -n "$(echo "$line" | tr -d ' ') ]] && echo "$line"
    done | sort -u
    echo ""
  fi

  # Changed (update, change, refactor, migrate)
  CHANGED=$(git log "$RANGE" --pretty=format:"- %s" --grep="^update" 2>/dev/null; \
            git log "$RANGE" --pretty=format:"- %s" --grep="^change" 2>/dev/null; \
            git log "$RANGE" --pretty=format:"- %s" --grep="^refactor" 2>/dev/null; \
            git log "$RANGE" --pretty=format:"- %s" --grep="^migrate" 2>/dev/null; \
            git log "$RANGE" --pretty=format:"- %s" --grep="^perf" 2>/dev/null)
  if [[ -n "$CHANGED" ]]; then
    echo "### Changed"
    echo "$CHANGED" | while IFS= read -r line; do
      line=$(echo "$line" | sed -E 's/^- (update|change|refactor|migrate|perf)\(?[^)]*\)?[:\s]*/- /I' | sed 's/\.$//')
      [[ -n "$(echo "$line" | tr -d ' ') ]] && echo "$line"
    done | sort -u
    echo ""
  fi

  # Removed (remove, delete, deprecate)
  REMOVED=$(git log "$RANGE" --pretty=format:"- %s" --grep="^remove" 2>/dev/null; \
            git log "$RANGE" --pretty=format:"- %s" --grep="^delete" 2>/dev/null; \
            git log "$RANGE" --pretty=format:"- %s" --grep="^deprecat" 2>/dev/null)
  if [[ -n "$REMOVED" ]]; then
    echo "### Removed"
    echo "$REMOVED" | while IFS= read -r line; do
      line=$(echo "$line" | sed -E 's/^- (remove|delete|deprecat)\(?[^)]*\)?[:\s]*/- /I' | sed 's/\.$//')
      [[ -n "$(echo "$line" | tr -d ' ') ]] && echo "$line"
    done | sort -u
    echo ""
  fi

  # 如果没有任何分类，显示原始commit列表
  if [[ -z "$ADDED$FIXED$CHANGED$REMOVED" ]]; then
    echo "### Commits"
    git log "$RANGE" --pretty=format:"- %s" 2>/dev/null | sort -u
    echo ""
  fi

  echo "---"
  echo ""
  echo "*此 CHANGELOG 由 [changelog.sh](https://github.com/claude-builders-bounty/claude-builders-bounty) 自动生成*"

} > "$OUTPUT_FILE"

echo "✅ CHANGELOG.md 已生成 (${COUNT} 次提交)"
echo "📄 输出: $OUTPUT_FILE"

# 生成样本输出（供PR使用）
cat "$OUTPUT_FILE"
