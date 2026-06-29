# Test Evidence

The hook was exercised locally with JSON payloads that match Claude Code `PreToolUse` input shape.

| Command | Expected | Result |
| --- | --- | --- |
| `echo ok` | allow | allow |
| `rm -rf build` | block | block |
| `rm -fr build` | block | block |
| `psql -c "DROP TABLE users"` | block | block |
| `git push --force origin main` | block | block |
| `sqlite3 app.db "DELETE FROM users"` | block | block |
| `sqlite3 app.db "DELETE FROM users WHERE id=1"` | allow | allow |
| `sqlite3 app.db "TRUNCATE sessions"` | block | block |

Blocked commands produced entries in `~/.claude/hooks/blocked.log` containing timestamp, attempted command, project path, and reason.
