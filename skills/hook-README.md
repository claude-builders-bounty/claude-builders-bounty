# Security Hook: Pre-tool-use — Block Destructive Commands

A Claude Code `pre-tool-use` hook that automatically blocks dangerous bash commands
before they are executed. Supports both Python and Bash versions.

## Installation

```bash
# Option 1: Python (recommended — richer logging)
cp skills/pre-tool-use.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use

# Option 2: Bash (lighter)
cp skills/pre-tool-use-hook.sh ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

That's it. Claude Code will automatically run this hook before every tool call.

## What It Blocks

| Pattern | Example | Severity |
|---------|---------|----------|
| `rm -rf` | `rm -rf /` | 🔴 Data loss |
| `DROP TABLE` | `DROP TABLE users` | 🟠 Data loss |
| `git push --force` | `git push --force origin main` | 🟠 History rewrite |
| `TRUNCATE` | `TRUNCATE orders` | 🟠 Data loss |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` | 🟠 Data loss |
| `sudo rm` | `sudo rm -rf /etc` | 🔴 System damage |
| `chmod -R 777` | `chmod -R 777 /var` | 🟠 Security risk |
| Fork bombs | `:(){ :\|:& };:` | 🔴 System crash |

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (ISO 8601 UTC)
- Command that was blocked
- Project path where it was attempted

## Safety

This hook **only** blocks the specific dangerous patterns listed above.
All normal bash commands pass through without interference.
