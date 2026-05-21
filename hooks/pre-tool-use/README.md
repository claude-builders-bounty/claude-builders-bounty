# Claude Code Safety Hook — Block Destructive Bash Commands

A `pre-tool-use` hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks) that intercepts dangerous bash commands before they execute.

## What it blocks

| Pattern | Example | Reason |
|---------|---------|--------|
| `rm -rf` | `rm -rf /tmp/old` | Recursive force delete — can destroy entire directories |
| `DROP TABLE` | `DROP TABLE users` | Permanently deletes a database table |
| `TRUNCATE` | `TRUNCATE TABLE logs` | Permanently empties a database table |
| `git push --force` | `git push --force origin main` | Can overwrite remote history |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` | Deletes all rows in a table |

## Install

```bash
# 1. Copy the hook script
mkdir -p ~/.claude/hooks/pre-tool-use
curl -o ~/.claude/hooks/pre-tool-use/block-destructive-commands.py \
  https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre-tool-use/block-destructive-commands.py

# 2. Make it executable
chmod +x ~/.claude/hooks/pre-tool-use/block-destructive-commands.py
```

## Configure

Add to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "pre_tool_use": [
      {
        "matcher": "Bash",
        "command": "python3 ~/.claude/hooks/pre-tool-use/block-destructive-commands.py"
      }
    ]
  }
}
```

## How it works

1. Claude Code calls the hook before every Bash tool execution
2. The hook checks the command against blocked patterns
3. If matched: the command is blocked, logged, and Claude receives an explanation
4. If safe: the command passes through normally

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log` in JSON format:

```json
{"timestamp": "2026-05-21T09:30:00+00:00", "command": "rm -rf /", "reason": "Recursive force delete", "project_path": "/home/user/project"}
```

## Testing

```bash
# Should be blocked (exit code 2):
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/old"}}' | python3 block-destructive-commands.py

# Should be allowed (exit code 0):
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 block-destructive-commands.py
```

## License

MIT
