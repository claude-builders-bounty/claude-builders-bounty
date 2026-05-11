# 🛡️ Claude Code Pre-Tool-Use Safety Hook

Blocks destructive bash commands before they execute in Claude Code.

## Installation

```bash
# 1. Create hooks directory
mkdir -p ~/.claude/hooks

# 2. Copy the hook
cp pre-tool-use-hook.sh ~/.claude/hooks/pre-tool-use-hook.sh && chmod +x ~/.claude/hooks/pre-tool-use-hook.sh
```

Then add to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "preToolUse": [
      {
        "matcher": "bash",
        "command": "~/.claude/hooks/pre-tool-use-hook.sh"
      }
    ]
  }
}
```

## What It Blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /` |
| `DROP TABLE` | `DROP TABLE users` |
| `TRUNCATE` | `TRUNCATE TABLE logs` |
| `DELETE FROM` without WHERE | `DELETE FROM users` |
| `git push --force` | `git push --force origin main` |
| `dd` to device | `dd if=/dev/zero of=/dev/sda` |
| `chmod -R 777 /` | `chmod -R 777 /` |
| Fork bombs | `:(){ :|:& }:` |

## How It Works

1. Reads the tool use event from stdin
2. Extracts the bash command
3. Checks against dangerous regex patterns
4. If matched: blocks execution, logs to `~/.claude/hooks/blocked.log`, explains why
5. If safe: allows execution

## Log Format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```json
{"timestamp":"2026-05-12T00:00:00Z","command":"rm -rf /","project_path":"/home/user/project","matched_pattern":"rm\\s+-rf"}
```

## Testing

```bash
# Should be blocked
echo '{"tool_input":{"command":"rm -rf /"}}' | ~/.claude/hooks/pre-tool-use-hook.sh

# Should be allowed
echo '{"tool_input":{"command":"ls -la"}}' | ~/.claude/hooks/pre-tool-use-hook.sh
```

## License

MIT
