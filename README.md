# pre-tool-use Hook for Claude Code

Blocks destructive bash commands before they execute.

## Installation

```bash
# 1. Create the hooks directory
mkdir -p ~/.claude/hooks

# 2. Save the hook
cp pre-tool-use.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## What it blocks

| Pattern | Example |
|---------|---------|
| Recursive delete | `rm -rf /` |
| Drop table | `DROP TABLE users` |
| Truncate | `TRUNCATE orders` |
| Force push | `git push --force` |
| Unqualified delete | `DELETE FROM users` (missing WHERE) |

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, project path, and command.
