# Safe Bash Hook — Opire $100 bounty entry (issue #3)

![bash](https://img.shields.io/badge/bash-hook-blue) ![tests](https://img.shields.io/badge/tests-32%2F32-green) ![license](https://img.shields.io/badge/license-MIT-green)

Claude Code `PreToolUse` hook: chặn lệnh nguy hiểm trước khi chạy, log mọi lần
chặn (timestamp | project path | command | reason), không đụng lệnh thường.

## Cài (2 lệnh)

```bash
./install.sh   # copy hook + merge idempotent vào ~/.claude/settings.json (giữ config cũ)
bash test-hook.sh
```

## Chặn gì

| Pattern | Ghi chú |
|---|---|
| `rm -rf` (mọi biến thể `-r`+`-f`, cả `sudo`, cả trong `bash -c`) | `rm -f` / `rm` thường cho qua |
| `DROP TABLE` / `TRUNCATE` | ngoài quotes; `grep 'DROP TABLE'` cho qua |
| `git push --force` / `-f` / refspec `+` / `push.force=true` | `--force-with-lease` cho qua |
| `DELETE`/`UPDATE` không `WHERE`, `WHERE 1=1`, `id=id`, comment `--` | `WHERE id=1` cho qua |
| `mkfs`, `dd of=/dev/`, `chmod -R 777 /`, `find -delete`, fork-bomb, `curl\|bash`, shutdown | — |

## Test thật
`bash test-hook.sh` → 32/32 xanh (block + allow + chống bypass). Samples: `samples/`.
