# Claude Code Safety Hook 🔒

A pre-tool-use hook for [Claude Code](https://claude.ai) that blocks dangerous bash commands before they execute.

## What It Blocks

| Pattern | Risk |
|---------|------|
| `rm -rf /` or `rm -rf <anything>` | Recursive file deletion |
| `DROP TABLE` | Irreversible database loss |
| `TRUNCATE` | Bulk data deletion |
| `DELETE FROM` without `WHERE` | Mass row deletion |
| `git push --force` | Branch history overwrite |
| `git reset --hard` | Commit history rewrite |
| `mkfs`, `fdisk`, `dd`, `format` | Disk formatting |
| `chmod 777 /` | Root permissions escalation |

Safe operations like `rm -rf node_modules` or `rm -rf target/` pass through normally.

## Installation

```bash
# 1. Install the hook
mkdir -p ~/.claude/hooks && cp safety-hook.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/safety-hook.py

# 2. Register the hook in Claude Code settings
cp settings.json ~/.claude/settings.json
```

**That's it.** Restart Claude Code. The hook activates on your next session.

> ⚠️ If `~/.claude/settings.json` already exists, merge the `hooks` block rather than overwriting.

## How It Works

Claude Code fires a `PreToolUse` event before every tool call. The hook:

1. Receives the tool call as JSON on stdin
2. Checks bash commands against dangerous patterns
3. **Blocked**: Logs to `~/.claude/hooks/blocked.log` + returns `{"skip": true}` with explanation
4. **Safe**: Allows execution with zero overhead

## Blocked Log

Every blocked command is timestamped and logged:

```json
{"timestamp": "2026-05-29T05:00:00Z", "command": "rm -rf /important", "reason": "Recursive force delete (rm -rf)", "project_path": "/home/user/project"}
```

Log location: `~/.claude/hooks/blocked.log`

## Testing

```bash
# Simulate a blocked command
echo '{"event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"rm -rf /etc"}}' | python3 ~/.claude/hooks/safety-hook.py

# Simulate a safe command (no output = allowed)
echo '{"event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 ~/.claude/hooks/safety-hook.py
```

## License

MIT
