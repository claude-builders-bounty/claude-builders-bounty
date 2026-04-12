# Safety First: Claude Code Security Hook

This hook intercepts and blocks dangerous bash commands before they are executed by Claude Code.

## Blocked Commands:
- `rm -rf`
- `DROP TABLE` (SQL)
- `git push --force`
- `TRUNCATE` (SQL)
- `DELETE FROM` without a `WHERE` clause

## Installation:

1. Create the hooks directory:
```bash
mkdir -p ~/.claude/hooks
```

2. Copy the hook script:
```bash
cp security_hook.py ~/.claude/hooks/pre-tool-use.py
```

## Logs:
All blocked attempts are logged to `~/.claude/hooks/blocked.log`.
