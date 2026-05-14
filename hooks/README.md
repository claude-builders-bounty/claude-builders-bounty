# Pre-Tool-Use Hook: Block Destructive Commands

A Claude Code `PreToolUse` hook that intercepts and blocks dangerous shell commands before execution.

## What It Blocks

| Category | Examples |
|----------|----------|
| File destruction | `rm -rf`, `shred`, `mkfs` |
| Database drops | `DROP TABLE`, `TRUNCATE`, `DELETE FROM` without `WHERE` |
| Git force operations | `git push --force`, `git reset --hard` |
| System commands | `shutdown`, `reboot`, `chmod 777` |
| Code injection | `curl \| bash`, `wget \| sh` |

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre_tool_use.py https://raw.githubusercontent.com/aagear/claude-builders-bounty/main/hooks/pre_tool_use.py
```

Add to `.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": ["python3 ~/.claude/hooks/pre_tool_use.py"]
      }
    ]
  }
}
```

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- ISO timestamp
- Blocked reason
- Full command
- Project path

## Customization

Edit the `BLOCKED_PATTERNS` list in the script to add/remove patterns. Each entry is a `(regex, reason)` tuple.
