# Claude Code Security Hook

A pre-tool-use hook that intercepts and blocks destructive bash commands.

## Installation

Run these commands to install the hook:

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

## Blocked Commands

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` (without a WHERE clause)

All blocked attempts are logged to `~/.claude/hooks/blocked.log`.
