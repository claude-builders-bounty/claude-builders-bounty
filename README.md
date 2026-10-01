# Pre-Tool-Use Hook — Block Destructive Bash Commands

Claude Code pre-tool-use hook that intercepts dangerous bash commands before execution.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hook.py ~/.claude/hooks/pre-tool-use-block-destructive.py
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "tool": "Bash",
        "command": "python3 ~/.claude/hooks/pre-tool-use-block-destructive.py"
      }
    ]
  }
}
```

## What It Blocks

| Pattern | Example |
|---|---|
| rm -rf / --recursive --force | rm -rf /tmp/foo |
| DROP TABLE | DROP TABLE users |
| git push --force / -f | git push origin main --force |
| TRUNCATE | TRUNCATE TABLE users |
| DELETE FROM (no WHERE) | DELETE FROM users |

## What It Allows

- Normal bash commands (ls, cat, echo, etc.)
- DELETE FROM with a WHERE clause
- All other non-destructive operations

## Logging

Every blocked attempt is logged to ~/.claude/hooks/blocked.log:

```
[2026-03-27T12:00:00+00:00] command="rm -rf /" project="/home/user/myproject"
```

## Testing

```bash
python3 test_hook.py
```

## Requirements

- Python 3.8+
- No external dependencies
