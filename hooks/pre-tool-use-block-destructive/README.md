# Pre-tool-use Hook: Block Destructive Commands

Blocks dangerous bash commands before they execute in Claude Code.

## Install

```bash
cp pre-tool-use ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use
```

## Blocked Patterns
- `rm -rf` — recursive force delete
- `DROP TABLE` — destructive SQL
- `git push --force` — force push
- `TRUNCATE` — table truncation
- `DELETE FROM` without WHERE clause
- `DROP DATABASE / DROP SCHEMA`
- `FORMAT` drive commands
- `shutdown -h / -r / -now`

## Logs
All blocked attempts logged to `~/.claude/hooks/blocked.log` with timestamps.
