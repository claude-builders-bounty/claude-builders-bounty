# Block Destructive Commands Hook

A Claude Code `pre-tool-use` hook that blocks dangerous bash commands.

## Installation (2 commands)

```bash
# 1. Copy the hook script
cp -r skills/block-destructive-hook/scripts/block_destructive.py ~/.claude/hooks/

# 2. Make it executable
chmod +x ~/.claude/hooks/block_destructive.py
```

## What gets blocked

- `rm -rf` — recursive force delete
- `DROP TABLE` / `TRUNCATE TABLE` — database destruction
- `git push --force` — force push to remote
- `DELETE FROM table;` — DELETE without WHERE clause
- `shred`, `dd of=/dev/` — secure deletion / disk writes

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## Requirements

- Python 3.7+
- Claude Code with hook support

## References

- Claude Code hooks docs: https://docs.anthropic.com/claude-code/hooks