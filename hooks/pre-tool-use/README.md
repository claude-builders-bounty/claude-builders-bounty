# Pre-Tool-Use Hook: Block Destructive Commands

Blocks dangerous bash commands before they execute in Claude Code.

## Install

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
cp block_destructive.py ~/.claude/hooks/pre-tool-use/
chmod +x ~/.claude/hooks/pre-tool-use/block_destructive.py
```

## What It Blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /` |
| `DROP TABLE` | `DROP TABLE users;` |
| `git push --force` | `git push --force main` |
| `TRUNCATE` | `TRUNCATE TABLE orders;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` |

## Logging

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Attempted command
- Project path
