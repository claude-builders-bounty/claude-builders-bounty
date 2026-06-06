#!/bin/bash
# 🦞 SafeGuard Hook - Claude Code pre-tool-use hook
# Bounty: $100
#
# 拦截危险的bash命令，在Claude Code执行前阻止它们
#
# 安装:
#   mkdir -p ~/.claude/hooks/
#   cp pre-tool-use.sh ~/.claude/hooks/pre-tool-use
#   chmod +x ~/.claude/hooks/pre-tool-use
#
# 日志: ~/.claude/hooks/blocked.log

set -euo pipefail

LOG_FILE="$HOME/.claude/hooks/blocked.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
PROJECT_PATH=$(pwd)

# ====== 危险模式定义 ======
# 这些模式匹配会直接阻止命令执行

DESTRUCTIVE_PATTERNS=(
  # 删除操作
  'rm[[:space:]]+-rf'
  'rm[[:space:]]+-fr'
  'rm[[:space:]]+--recursive'
  'rm[[:space:]]+[a-zA-Z0-9_/.-]*[[:space:]]+-rf'
  'rm[[:space:]]+-rf[[:space:]]+/'
  'rm[[:space:]]+-rf[[:space:]]+[.]*'
  'rm[[:space:]]+-rf[[:space:]]+~'
  
  # Git破坏性操作
  'git[[:space:]]+push[[:space:]]+--force'
  'git[[:space:]]+push[[:space:]]+-f[[:space:]]'
  'git[[:space:]]+reset[[:space:]]+--hard'
  'git[[:space:]]+branch[[:space:]]+-D'
  'git[[:space:]]+clean[[:space:]]+-f[d]?'
  'git[[:space:]]+rebase[[:space:]]+--[a-z]*[[:space:]]+--[a-z]*'
  
  # 数据库危险
  'DROP[[:space:]]+TABLE'
  'DROP[[:space:]]+DATABASE'
  'TRUNCATE[[:space:]]+TABLE'
  'DELETE[[:space:]]+FROM[[:space:]]+[a-zA-Z_]+[[:space:]]*;'
  'DELETE[[:space:]]+FROM[[:space:]]+[a-zA-Z_]+[[:space:]]*$'
  
  # 系统操作
  'dd[[:space:]]+if='
  'mkfs\.[a-z]'
  'fdisk'
  '> /dev/[a-z]'
  ':\(\)[[:space:]]*{[[:space:]]*:'
  'chmod[[:space:]]+000'
  'chown[[:space:]]+-R'
  'wget[[:space:]]+.*[|].*sh'
  'curl[[:space:]]+.*[|].*sh'
  
  # 危险链接
  'ln[[:space:]]+-sf'
)

# ====== 输入分析 ======
# Claude Code传递命令作为参数，获取完整命令字符串
COMMAND="$*"

# ====== 检查命令是否危险 ======
BLOCKED=false
BLOCKED_REASON=""

for pattern in "${DESTRUCTIVE_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    BLOCKED=true
    BLOCKED_REASON="匹配危险模式: $pattern"
    break
  fi
done

# 额外安全检查: rm -rf 后的参数不应包含 /, ~, .., .*
if [[ "$COMMAND" =~ rm[[:space:]]+-rf[[:space:]]+([a-zA-Z0-9_./~-]+) ]]; then
  TARGET="${BASH_REMATCH[1]}"
  if [[ "$TARGET" == "/" || "$TARGET" == "~" || "$TARGET" == "." || "$TARGET" == ".." ]]; then
    BLOCKED=true
    BLOCKED_REASON="rm -rf 目标指向危险路径: $TARGET"
  fi
fi

# 检查没有 WHERE 条件的 SQL DELETE
if echo "$COMMAND" | grep -qiE 'DELETE[[:space:]]+FROM'; then
  if ! echo "$COMMAND" | grep -qi 'WHERE'; then
    BLOCKED=true
    BLOCKED_REASON="DELETE FROM 缺少 WHERE 子句"
  fi
fi

# ====== 执行拦截或放行 ======
if [[ "$BLOCKED" == true ]]; then
  # 记录到日志
  LOG_DIR="$(dirname "$LOG_FILE")"
  mkdir -p "$LOG_DIR"
  echo "[$TIMESTAMP] 已阻止 | 项目: $PROJECT_PATH | 原因: $BLOCKED_REASON | 命令: $COMMAND" >> "$LOG_FILE"
  
  # 输出阻止信息给Claude
  echo ""
  echo "========================================================================"
  echo "  🛑 命令已被 SafeGuard Hook 阻止"
  echo "========================================================================"
  echo ""
  echo "  命令: $COMMAND"
  echo "  原因: $BLOCKED_REASON"
  echo "  时间: $TIMESTAMP"
  echo "  项目: $PROJECT_PATH"
  echo ""
  echo "  💡 如需执行此操作，请使用更安全的方式:"
  echo "     - 使用 'trash' 替代 'rm' (可恢复)"
  echo "     - 使用 'git push --force-with-lease' 替代 'git push --force'"
  echo "     - 确认 WHERE 子句后再执行 DELETE"
  echo ""
  echo "  📝 已记录到: $LOG_FILE"
  echo "========================================================================"
  echo ""
  
  # 关键: 返回非0会阻止命令执行
  exit 1
fi

# ====== 安全命令直接放行 ======
exit 0
