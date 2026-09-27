#!/usr/bin/env bash
# test-hook.sh — kiểm tra block-dangerous.sh: 5 pattern chặn + lệnh thường cho qua.
cd "$(dirname "$0")"
HOOK=./block-dangerous.sh
export BLOCKED_LOG=/tmp/blocked-test.log
rm -f "$BLOCKED_LOG"
pass=0; fail=0
chk() { # $1: tên $2: lệnh $3: expect exit (2=chặn, 0=qua)
  out=$(echo "{\"tool_input\":{\"command\":\"$2\"},\"cwd\":\"/tmp/demo\"}" | bash "$HOOK" 2>&1)
  code=$?
  if [[ $code -eq $3 ]]; then pass=$((pass+1)); echo "XANH $1 (exit $code)"; else fail=$((fail+1)); echo "ĐỎ $1 (muốn $3, được $code): $out"; fi
}
chk "rm-rf" "rm -rf /tmp/x" 2
chk "sudo-rm-rf" "sudo rm -rf /" 2
chk "drop-table" "psql -c 'DROP TABLE users'" 2
chk "truncate" "mysql -e 'TRUNCATE sessions'" 2
chk "push-force" "git push --force origin main" 2
chk "push-f" "git push -f origin main" 2
chk "delete-no-where" "psql -c 'DELETE FROM users'" 2
chk "ls-thuong" "ls -la /tmp" 0
chk "git-status" "git status" 0
chk "delete-co-where" "psql -c \"DELETE FROM users WHERE id=1\"" 0
chk "rm-thuong" "rm /tmp/file.txt" 0
echo "--- blocked.log ($(wc -l < "$BLOCKED_LOG") dòng) ---"; head -3 "$BLOCKED_LOG"
echo "KQ: $pass xanh / $fail đỏ"
[[ $fail -eq 0 ]]
