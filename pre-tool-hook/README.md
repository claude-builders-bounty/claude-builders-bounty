# PreToolUse Hook: Destructive Command Blocker

A Claude Code security hook that intercepts and blocks dangerous bash commands before execution.

## Installation (2 steps)

1. Copy `protect.py` to `~/.claude/hooks/protect.py` and make it executable:
   ```bash
   mkdir -p ~/.claude/hooks
   cp protect.py ~/.claude/hooks/protect.py
   chmod +x ~/.claude/hooks/protect.py
   ```
2. Register the hook in your Claude Code config:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/protect.py"
          }
        ]
      }
    ]
  }
}
```

## Blocked Patterns
- `rm -rf` / `rm -f`
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with a UTC timestamp, reason, command, and working directory. Normal bash commands pass through untouched.
