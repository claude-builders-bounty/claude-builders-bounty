# block-destructive-bash — Claude Code PreToolUse hook

A [Claude Code](https://docs.anthropic.com/claude-code) `PreToolUse` hook that
**blocks destructive shell commands before they run** and logs every attempt.

Blocked patterns: `rm -rf` · `git push --force` (`-f`) · `DROP TABLE` · `TRUNCATE` ·
`DELETE FROM` without a `WHERE` clause. Everything else is untouched — including the
safe `git push --force-with-lease` and bounded `DELETE ... WHERE ...`.

## Install (2 commands)
```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty && cd claude-builders-bounty
bash hooks/install.sh
```

`install.sh` copies the hook to `~/.claude/hooks/` and registers it as a `PreToolUse`
hook for the `Bash` tool in `~/.claude/settings.json` (idempotent).

## What gets blocked
| Pattern | Example that is blocked |
|---|---|
| `rm -rf` (recursive + force, any order) | `rm -rf build`, `rm --recursive --force node_modules` |
| force push | `git push --force origin main`, `git push -f` |
| `DROP TABLE` | `psql -c 'DROP TABLE users'` |
| `TRUNCATE` | `mysql -e 'TRUNCATE logs'` |
| `DELETE FROM` without `WHERE` | `sqlite3 app.db 'DELETE FROM sessions'` |

When blocked, Claude sees a clear message explaining why, e.g.:

```
BLOCKED by block-destructive-bash hook.
Reason: recursive, forced file deletion (`rm -rf`)
Command: rm -rf build
Logged to: /home/you/.claude/hooks/blocked.log
```

## Log
Each blocked attempt is appended to `~/.claude/hooks/blocked.log` as
`<utc-timestamp>\t<project-path>\t<command>`.

## Verify it works
```bash
python3 hooks/validate_hook.py   # deterministic acceptance check; prints VALIDATION_OK
```

## Uninstall
Delete `~/.claude/hooks/block_destructive_bash.py` and remove the `PreToolUse`
entry it added to `~/.claude/settings.json`.
