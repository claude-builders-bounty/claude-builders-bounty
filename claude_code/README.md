# Pre-tool-use Hook for Claude Code

## Installation
```bash
mkdir -p ~/.claude/hooks
cp claude-hook.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## What it blocks
- `rm -rf` commands
- `git push --force` or `git push -f`
- `DROP TABLE`
- `TRUNCATE TABLE`
- `DELETE FROM` without WHERE clause

## Logging
All blocked attempts logged to `~/.claude/hooks/blocked.log`
