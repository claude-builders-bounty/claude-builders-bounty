# PreToolUse Hook - Block Dangerous Commands

A Claude Code hook that intercepts and blocks dangerous bash commands before execution.

## What It Blocks

| Pattern | Description |
|---------|-------------|
| `rm -rf` | Recursive force deletion |
| `DROP TABLE` | Database table deletion |
| `git push --force` | Force push to remote |
| `TRUNCATE` | Table truncation |
| `DELETE FROM` (without WHERE) | Mass deletion |

## Installation

```bash
# 1. Copy the hook script
cp hooks/block-dangerous-commands.py ~/.claude/hooks/

# 2. Add to ~/.claude/settings.json:
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-dangerous-commands.py"
          }
        ]
      }
    ]
  }
}
```

## How It Works

1. **Intercepts**: Every Bash tool call before execution
2. **Analyzes**: Checks command against blocked patterns
3. **Blocks**: If dangerous, shows error and logs attempt
4. **Allows**: Safe commands pass through unchanged

## Logging

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Attempted command
- Project path
- Reason for blocking

## Testing

Test with these commands:
```bash
# Should be BLOCKED
rm -rf /
DROP TABLE users;
git push --force
TRUNCATE TABLE logs;
DELETE FROM users;

# Should be ALLOWED
ls -la
git push
DELETE FROM users WHERE id = 1;
```

## Exit Codes

- `0`: Command allowed (passes through)
- `2`: Command blocked (shows error message)

---
*Created for Claude Builders Bounty - Issue #3*
