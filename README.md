# block-destructive

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before execution.

## What It Blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` / `rm -r` | `rm -rf /` |
| `DROP TABLE` | `DROP TABLE users;` |
| `TRUNCATE` | `TRUNCATE TABLE logs;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` |
| `git push --force` | `git push --force origin main` |
| `git push -f` | `git push -f` |
| `git push --force-with-lease` | `git push --force-with-lease` |

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.

## Installation

```bash
# 1. Copy the hook script
mkdir -p ~/.claude/hooks && cp block-destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.py

# 2. Add to your Claude Code settings (~/.claude/settings.json)
# Add this to the "hooks" section:
```

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "preToolUse": [
      {
        "type": "command",
        "command": "python3 ~/.claude/hooks/block-destructive.py",
        "matcher": "Bash"
      }
    ]
  }
}
```

That's it! Claude Code will now block destructive commands and log attempts.

## How It Works

1. Claude Code triggers the hook before every `Bash` tool use
2. The hook reads the command from stdin (JSON format)
3. It checks the command against a list of dangerous patterns (regex)
4. If matched, it outputs a block decision with an explanation
5. Blocked attempts are logged with timestamp, command, and project path

## Log Format

```
[2026-05-22T12:00:00.000000Z] BLOCKED: rm -rf: Recursive force delete is blocked
  Command: rm -rf /var/log/*
  Project: /home/user/my-project
```

## Testing

```bash
# Test the hook manually
echo '{"tool_input":{"command":"rm -rf /"}}' | python3 block-destructive.py
# Output: {"decision":"block","reason":"⛔ Blocked: rm -rf: Recursive force delete is blocked..."}

echo '{"tool_input":{"command":"ls -la"}}' | python3 block-destructive.py
# No output, exit 0 = allowed
```

## License

MIT
