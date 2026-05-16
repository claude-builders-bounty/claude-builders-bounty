# Destructive Bash guard for Claude Code

A `PreToolUse` hook that blocks dangerous Bash commands before Claude Code runs them.

It blocks:
- `rm -rf` / `rm -fr` / separate recursive+force flags such as `rm -r -f`
- `DROP TABLE`
- `git push --force` / `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a timestamp, attempted command, project path, and block reason.

## Install

```bash
python3 hooks/install.py
```

The installer copies the hook to `~/.claude/hooks/block-destructive-bash.py`, makes it executable, and idempotently adds the Bash `PreToolUse` matcher to `~/.claude/settings.json`.

Run Claude Code normally. Safe Bash commands pass through silently; blocked commands return a `permissionDecision: deny` response with a clear reason Claude can act on.


SQL safeguards are scoped to direct SQL commands or common SQL clients (`psql`, `mysql`, `mariadb`, `sqlite3`, `sqlcmd`) to avoid blocking harmless shell text such as `echo "DROP TABLE"`.
