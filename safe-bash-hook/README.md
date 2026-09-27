# Safe Bash Hook — Opire $100 bounty entry (issue #3)

![bash](https://img.shields.io/badge/bash-hook-blue) ![tests](https://img.shields.io/badge/tests-11%2F11-green) ![license](https://img.shields.io/badge/license-MIT-green)

Claude Code `PreToolUse` hook: chặn lệnh nguy hiểm trước khi chạy, log mọi lần
chặn, không đụng lệnh thường.

## Cài (2 lệnh)

```bash
mkdir -p ~/.claude/hooks && cp block-dangerous.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-dangerous.sh
echo '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"~/.claude/hooks/block-dangerous.sh"}]}]}}' > ~/.claude/hooks.json
```

## Chặn gì

| Pattern | Lý do |
|---|---|
| `rm -rf` (+ `sudo`) | sai 1 ký tự là mất hệ thống |
| `DROP TABLE` / `TRUNCATE` | xóa dữ liệu không rollback |
| `git push --force` / `-f` | viết lại lịch sử remote |
| `DELETE FROM` không `WHERE` | xóa cả bảng |

`DELETE ... WHERE`, `rm file`, `ls`, `git status` cho qua bình thường.
Mỗi lần chặn: exit 2 + message cho Claude + 1 dòng vào
`~/.claude/hooks/blocked.log` (timestamp | project path | command).

## Test thật
`bash test-hook.sh` → 11/11 xanh (7 case chặn + 4 case cho qua, log đủ timestamp/cwd/command).
