# Pre-Tool-Use Hook: Destructive Command Guard

Blocks dangerous bash commands before they execute in Claude Code.

## Installation

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use
```

## What it blocks

- `rm -rf` (recursive delete)
- `DROP TABLE` (destructive schema)
- `git push --force` (history rewrite)
- `TRUNCATE` (destructive data op)
- `DELETE FROM` without `WHERE`

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp,
command, and project path.
