# Pre-Tool-Use Hook: Block Destructive Commands

Intercepts dangerous bash commands before execution and logs blocked attempts.

## Installation

```bash
# 1. Create hooks directory
mkdir -p ~/.claude/hooks

# 2. Copy hook
cp pre-tool-use.sh ~/.claude/hooks/

# 3. Make executable
chmod +x ~/.claude/hooks/pre-tool-use.sh
```

## What it blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive delete |
| `DROP TABLE` | SQL destruction |
| `TRUNCATE` | SQL data loss |
| `DELETE FROM` (no WHERE) | SQL mass delete |
| `git push --force` | Force push |
| `git push -f` | Force push shorthand |

## Log Format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
2024-01-15T10:30:00Z | rm -rf / | /home/user/project
2024-01-15T10:31:00Z | DROP TABLE users; | /home/user/project
```

## Message to Claude

When a command is blocked, the hook returns:

```
BLOCKED: [command] matches destructive pattern [pattern]
Reason: [explanation]
```

This prevents execution and explains why.