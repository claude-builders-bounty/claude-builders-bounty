# Safety Hook — blocks destructive bash commands

A Claude Code `PreToolUse` hook that intercepts dangerous bash commands
**before** they are executed.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use.py
```

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "~/.claude/hooks/pre-tool-use.py" }
        ]
      }
    ]
  }
}
```

Done. Restart Claude Code.

## What it blocks

| Pattern | Example |
|---|---|
| `rm -rf` | `rm -rf /`, `rm -rf node_modules` |
| Force pushes | `git push --force` |
| Destructive SQL | `DROP TABLE users`, `TRUNCATE logs` |
| Unsafe DELETE | `DELETE FROM users` (no `WHERE`/`LIMIT`) |
| Nuclear FS ops | `mkfs /dev/sda`, `chmod -R 777 /` |

Normal bash commands (`ls`, `npm test`, `git commit`, `SELECT * FROM users WHERE id = 1`) are **never** affected.

## What happens when blocked

1. Claude receives a clear message explaining why the command was blocked.
2. Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
2026-08-10T14:03:22+07:00 | project=/home/dev/app | blocked=rm -rf node_modules
```

Timestamp, attempted command, and project path — ready for audit.

## Test it yourself

```bash
# Should BLOCK (exit 2 + JSON with decision=block):
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"},"cwd":"/tmp"}' | python3 pre-tool-use.py

# Should ALLOW (exit 0):
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp"}' | python3 pre-tool-use.py

# SQL safety: DELETE with WHERE is allowed, without WHERE is blocked:
echo '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM users WHERE id = 1"},"cwd":"/tmp"}' | python3 pre-tool-use.py
```

## Requirements

- Python 3.8+
- Claude Code CLI
