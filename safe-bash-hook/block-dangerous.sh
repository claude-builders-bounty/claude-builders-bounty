#!/usr/bin/env bash
# block-dangerous.sh — Claude Code PreToolUse hook: chặn lệnh bash nguy hiểm.
# Cài: copy vào ~/.claude/hooks/ + khai báo hooks.json (xem README).
# Vào: JSON qua stdin {"tool_input":{"command":"..."},"cwd":"..."}.
# Ra: exit 0 = cho qua; exit 2 + stderr = chặn (stderr hiện cho Claude đọc).
# Mọi lần chặn ghi vào ~/.claude/hooks/blocked.log: timestamp | cwd | command.
set -uo pipefail

LOG_FILE="${BLOCKED_LOG:-$HOME/.claude/hooks/blocked.log}"
INPUT=$(cat)
CMD=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")
CWD=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null || echo "")

block() { # $1: lý do
  mkdir -p "$(dirname "$LOG_FILE")"
  printf '%s | %s | %s\n' "$(date '+%F %T')" "${CWD:-?}" "$CMD" >> "$LOG_FILE"
  echo "BLOCKED: $1" >&2
  echo "Lệnh: $CMD" >&2
  echo "Hãy viết lại lệnh an toàn hơn (xem README mục patterns)." >&2
  exit 2
}

# 1. rm -rf (mọi biến thể có -r/-f kết hợp, kể cả sudo)
if echo "$CMD" | grep -Eq '(^|[;&|]|sudo[[:space:]]+)rm[[:space:]]+.*-[a-zA-Z]*[rR][a-zA-Z]*[fF]|-[a-zA-Z]*[fF][a-zA-Z]*[rR]'; then
  block "rm -rf có thể xóa cả hệ thống nếu sai đường dẫn. Hãy xóa file cụ thể, kiểm tra pwd trước."
fi
# 2. SQL phá hoại: DROP TABLE / TRUNCATE
if echo "$CMD" | grep -Eiq 'DROP[[:space:]]+TABLE|TRUNCATE[[:space:]]+(TABLE[[:space:]]+)?[a-zA-Z_]+'; then
  block "DROP TABLE/TRUNCATE xóa sạch dữ liệu không khôi phục được. Hãy dùng migration có rollback."
fi
# 3. git push --force (kể cả -f)
if echo "$CMD" | grep -Eq 'git[[:space:]]+push.*(--force|-[a-zA-Z]*f)'; then
  block "git push --force viết lại lịch sử remote, phá repo người khác. Hãy dùng --force-with-lease."
fi
# 4. DELETE FROM không có WHERE
if echo "$CMD" | grep -Eiq 'DELETE[[:space:]]+FROM'; then
  if ! echo "$CMD" | grep -Eiq 'WHERE'; then
    block "DELETE FROM không có WHERE xóa toàn bộ bảng. Hãy thêm WHERE hoặc dùng SELECT kiểm tra trước."
  fi
fi

exit 0
