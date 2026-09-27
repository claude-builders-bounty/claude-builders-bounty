# Samples — input JSON mẫu + kết quả chặn/cho qua (copy từ test-hook.sh chạy thật)

## Bị chặn (exit 2)
```
$ echo '{"tool_input":{"command":"rm -rf /tmp/x"},"cwd":"/tmp/demo"}' | bash block-dangerous.sh
BLOCKED: rm -rf/-r -f có thể xóa cả hệ thống nếu sai đường dẫn. ...
$ echo '{"tool_input":{"command":"psql -c '"'"'DELETE FROM users WHERE 1=1'"'"'"},"cwd":"/tmp/demo"}' | bash block-dangerous.sh
BLOCKED: WHERE luôn đúng ...
$ echo '{"tool_input":{"command":"git push --force origin main"},"cwd":"/tmp/demo"}' | bash block-dangerous.sh
BLOCKED: git push --force viết lại lịch sử remote ...
```

## Cho qua (exit 0)
`ls -la /tmp` · `git status` · `git push origin main` ·
`git push --force-with-lease origin main` · `rm -f /tmp/a.log` ·
`grep -r 'DROP TABLE' src/` (nhắc từ khóa trong quotes không tính)

## blocked.log (thật từ test)
```
2026-09-27 20:43:22 | /tmp/demo | rm -rf /tmp/x | rm -rf/-r -f ...
```
Full matrix: `bash test-hook.sh` → 32/32 xanh.
