# Destructive command hook test output

The hook was tested locally with Claude Code-style JSON payloads.

## Blocked examples

- `rm -rf build` exits `2`, prints a clear block message, and writes `rm -rf` to `~/.claude/hooks/blocked.log`.
- `DROP TABLE users;` exits `2` and logs `DROP TABLE`.
- `git push --force origin main` exits `2` and logs `git push --force`.
- `TRUNCATE audit_log;` exits `2` and logs `TRUNCATE`.
- `DELETE FROM users;` exits `2` and logs `DELETE FROM without WHERE`.

## Allowed examples

- `python3 -m pytest` exits `0`.
- `git status --short` exits `0`.
- `DELETE FROM users WHERE id = 1;` exits `0`.
- Non-Bash tool payloads exit `0`.
