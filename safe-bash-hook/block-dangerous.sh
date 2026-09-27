#!/usr/bin/env bash
# block-dangerous.sh — Claude Code PreToolUse hook: chặn lệnh bash nguy hiểm.
# Cài: bash install.sh (merge idempotent vào ~/.claude/settings.json, xem README).
# Vào: JSON qua stdin {"tool_input":{"command":"..."},"cwd":"..."}.
# Ra: exit 0 = cho qua; exit 2 + stderr = chặn (stderr hiện cho Claude đọc).
# Mọi lần chặn ghi vào ~/.claude/hooks/blocked.log: timestamp | cwd | command | reason.
set -uo pipefail

LOG_FILE="${BLOCKED_LOG:-$HOME/.claude/hooks/blocked.log}"
INPUT=$(cat)
CMD=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")
CWD=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null || echo "")

block() { # $1: lý do
  mkdir -p "$(dirname "$LOG_FILE")"
  printf '%s | %s | %s | %s\n' "$(date '+%F %T')" "${CWD:-?}" "$CMD" "$1" >> "$LOG_FILE"
  echo "BLOCKED: $1" >&2
  echo "Lệnh: $CMD" >&2
  echo "Hãy viết lại lệnh an toàn hơn (xem README mục patterns)." >&2
  exit 2
}

# Bóc wrapper: sudo/env/timeout + shell -c "..." -> quét cả lệnh trong.
SCAN="$CMD"
SCAN=$(echo "$SCAN" | sed -E 's/^([[:space:]]*(sudo|env|timeout[[:space:]]+[^ ]+)[[:space:]]+)+//')
INNER=$(echo "$SCAN" | sed -nE 's/^(bash|sh|zsh)[[:space:]]+(-[a-z]*c[[:space:]]+)?["'"'"'](.*)["'"'"'][[:space:]]*$/\3/p')
[[ -n "$INNER" ]] && SCAN="$SCAN
$INNER"

# Chuỗi trong quotes chỉ bỏ qua với lệnh chỉ nhắc từ khóa (echo/grep/printf/cat);
# SQL client (psql/mysql/sqlite) quét cả trong quotes vì đó là câu lệnh thật.
if echo "$SCAN" | grep -Eq '(^|[;&|])[[:space:]]*(echo|grep|printf|cat)[[:space:]]'; then
  SQLSCAN=$(echo "$SCAN" | sed -E "s/'[^']*'//g; s/\"[^\"]*\"//g")
else
  SQLSCAN="$SCAN"
fi
# Strip SQL comment để chống bypass: DELETE x -- WHERE / /* WHERE */
CODE=$(echo "$SQLSCAN" | sed -E 's/--[^\n]*$//; s:/\*.*\*/::g')

# 1. rm -rf: cần cả recursive (-r/-R) và force (-f), gộp hoặc tách (sudo đã bóc)
if echo "$SCAN" | grep -Eq '(^|[;&|])[[:space:]]*rm[[:space:]]+'; then
  FLAGS=$(echo "$SCAN" | grep -Eo 'rm[[:space:]]+(-[^;&|]+)?' | head -1 | grep -Eo '\-[a-zA-Z]+' | tr -d '\n')
  if echo "$FLAGS" | grep -q '[rR]' && echo "$FLAGS" | grep -q '[fF]'; then
    block "rm -rf/-r -f có thể xóa cả hệ thống nếu sai đường dẫn. Hãy xóa file cụ thể, kiểm tra pwd trước."
  fi
fi
# 2. SQL phá hoại: DROP TABLE / TRUNCATE (ngoài quotes, đã strip comment)
if echo "$CODE" | grep -Eiq 'DROP[[:space:]]+TABLE|TRUNCATE[[:space:]]+(TABLE[[:space:]]+)?[a-zA-Z_]+'; then
  block "DROP TABLE/TRUNCATE xóa sạch dữ liệu không khôi phục được. Hãy dùng migration có rollback."
fi
# 3. git push --force (nhưng KHÔNG chặn --force-with-lease)
if echo "$SCAN" | grep -Eq 'git[[:space:]]+.*push([[:space:]]|$)'; then
  if echo "$SCAN" | grep -Eq -- '--force(=[^[:space:]]+)?([[:space:]]|$)' && ! echo "$SCAN" | grep -Eq -- '--force-with-lease'; then
    block "git push --force viết lại lịch sử remote, phá repo người khác. Hãy dùng --force-with-lease."
  fi
  if echo "$SCAN" | grep -Eq '(^|[[:space:];])-([a-zA-Z]*f)([[:space:];]|$)'; then
    block "git push -f viết lại lịch sử remote, phá repo người khác. Hãy dùng --force-with-lease."
  fi
  if echo "$SCAN" | grep -Eq 'git[[:space:]]+push[[:space:]]+[^-]*\+[^[:space:]]*:'; then
    block "git push refspec kiểu +branch (force ngầm). Hãy dùng --force-with-lease."
  fi
  if echo "$SCAN" | grep -Eq -- '-c[[:space:]]+push\.force=true'; then
    block "push.force=true bật force mặc định — nguy hiểm. Hãy bỏ config này."
  fi
fi
# 4. DELETE/UPDATE không WHERE thật (chống WHERE 1=1, id=id, comment)
if echo "$CODE" | grep -Eiq 'DELETE[[:space:]]+FROM|UPDATE[[:space:]]+[a-zA-Z_]+[[:space:]]+SET'; then
  WHERE=$(echo "$CODE" | grep -Eio 'WHERE[[:space:]]+[^;]+' | head -1)
  if [[ -z "$WHERE" ]]; then
    block "DELETE/UPDATE không có WHERE ảnh hưởng toàn bộ bảng. Hãy thêm WHERE hoặc SELECT kiểm tra trước."
  fi
  if echo "$WHERE" | grep -Eiq '1[[:space:]]*=[[:space:]]*1|OR[[:space:]]+1=1'; then
    block "WHERE luôn đúng ($WHERE) tương đương không có WHERE. Hãy thu hẹp điều kiện."
  fi
  PAIR=$(echo "$WHERE" | grep -Eio '[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*=[[:space:]]*[a-zA-Z_][a-zA-Z0-9_]*' | head -1 || true)
  if [[ -n "$PAIR" ]]; then
    L=$(echo "$PAIR" | cut -d= -f1 | tr -d ' '); R=$(echo "$PAIR" | cut -d= -f2 | tr -d ' ')
    if [[ -n "$L" && "$L" == "$R" ]]; then
      block "WHERE $L=$R luôn đúng tương đương không có WHERE. Hãy thu hẹp điều kiện."
    fi
  fi
fi
# 5. Phá hệ thống / thực thi remote
if echo "$SCAN" | grep -Eiq '(^|[;&|])[[:space:]]*(mkfs(\.[a-z0-9]+)?|wipefs|fdisk)[[:space:]]'; then
  block "mkfs/wipefs/fdisk phá partition. Chạy tay ngoài agent nếu thật sự cần."
fi
if echo "$SCAN" | grep -Eiq 'dd[[:space:]]+.*of=/dev/'; then
  block "dd ghi trực tiếp device. Kiểm tra of= kỹ hoặc chạy tay."
fi
if echo "$SCAN" | grep -Eiq 'chmod[[:space:]]+-R[[:space:]]+777[[:space:]]+/|chown[[:space:]]+-R[[:space:]]+[^[:space:]]+[[:space:]]+/'; then
  block "chmod/chown đệ quy trên / phá quyền hệ thống."
fi
if echo "$SCAN" | grep -Eq 'find[[:space:]]+/?.*[[:space:]]-delete'; then
  block "find -delete trên cây lớn nguy hiểm như rm -rf. Hãy liệt kê trước (-print)."
fi
if echo "$SCAN" | grep -Eq ':\(\)\{[^}]*:[|:][^}]*\}[;&]?'; then
  block "fork-bomb. Từ chối."
fi
if echo "$SCAN" | grep -Eq 'curl[^\n|]*\|[[:space:]]*(bash|sh)|wget[^\n|]*\|[[:space:]]*(bash|sh)'; then
  block "curl|bash chạy code remote không verify. Hãy tải về, đọc rồi mới chạy."
fi
if echo "$SCAN" | grep -Eiq '(^|[;&|])[[:space:]]*(shutdown|halt|poweroff|reboot)([[:space:]]|$)'; then
  block "shutdown/reboot giết máy agent đang chạy. Chạy tay nếu cần."
fi

exit 0
