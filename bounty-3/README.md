# Bounty #3: Pre-tool-use Hook Blocking Destructive Commands

A Claude Code pre-tool-use hook that intercepts and blocks destructive bash commands before they execute.

## What It Blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` / `rm -fr` | `rm -rf /` |
| `DROP TABLE` | `DROP TABLE users;` |
| `git push --force` / `-f` | `git push --force origin main` |
| `TRUNCATE` | `TRUNCATE TABLE users;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` |

All checks are case-insensitive and handle multiline commands and SQL comments.

## Install (2 commands)

```bash
# 1. Copy the hook script
mkdir -p ~/.claude/hooks && cp bounty-3/pre_tool_use_hook.py ~/.claude/hooks/

# 2. Add to your Claude Code settings (~/.claude/settings.json)
# Under "hooks", add:
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
            "command": "python3 ~/.claude/hooks/pre_tool_use_hook.py"
          }
        ]
      }
    ]
  }
}
```

## Hook Format

Claude Code hooks receive JSON on stdin:

```json
{
  "tool_name": "Bash",
  "tool_input": {"command": "rm -rf /"},
  "project_path": "/home/user/my-project"
}
```

Output JSON on stdout:

- **Allow:** `{"decision": "allow"}`
- **Block:** `{"decision": "block", "reason": "⛔ Blocked: rm with force flag detected"}`

Blocked attempts are logged to `~/.claude/hooks/blocked.log`.

## Run Tests

```bash
python3 bounty-3/test_hook.py
```

## License

MIT
