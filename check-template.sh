#!/usr/bin/env bash
# check-template.sh — self-check: mọi path/lệnh trong CLAUDE.md đều nhất quán.
cd "$(dirname "$0")"
pass=0; fail=0
chk() { if eval "$2"; then pass=$((pass+1)); echo "XANH $1"; else fail=$((fail+1)); echo "ĐỎ $1"; fi; }
chk "có đủ 5 sections" "grep -q 'Dev commands' CLAUDE.md && grep -q 'Folder structure' CLAUDE.md && grep -q 'migration' CLAUDE.md && grep -q 'Component patterns' CLAUDE.md && grep -q \"What we DON'T do\" CLAUDE.md"
chk "mọi rule anti-pattern có lý do" "! grep -A1 '^- Không' CLAUDE.md | grep -q '^--'"
chk "pin version đầy đủ" "grep -q 'next@15' CLAUDE.md && grep -q 'better-sqlite3@12' CLAUDE.md && grep -q 'node@22' CLAUDE.md"
chk "migration bất biến" "grep -q 'KHÔNG sửa file đã merge' CLAUDE.md"
chk "test greenfield" "mkdir -p /tmp/greenfield-test && cp CLAUDE.md /tmp/greenfield-test/ && test -f /tmp/greenfield-test/CLAUDE.md"
echo "KQ: $pass xanh / $fail đỏ"
[[ $fail -eq 0 ]]
