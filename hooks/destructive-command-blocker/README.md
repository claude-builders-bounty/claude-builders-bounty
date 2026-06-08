# Destructive Command Blocker (pre-tool-use hook)

Blocks destructive bash commands in Claude Code before execution.

## Installation

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use.sh
```

## What It Blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /` or `rm -rf node_modules` |
| `DROP TABLE` | `DROP TABLE users;` |
| `git push --force` | `git push --force origin main` |
| `TRUNCATE TABLE` | `TRUNCATE TABLE logs;` |
| `DELETE FROM` without WHERE | `DELETE FROM users;` |

## Logging

All blocked commands are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Blocked command
- Project directory

## Safe Alternatives

- `git push --force-with-lease` instead of `git push --force`
- Application-level delete operations instead of direct DB drops
- `TRUNCATE` with application confirmation instead of bare SQL

Bounty: $100 — claude-builders-bounty issue #3
