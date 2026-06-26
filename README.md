# Destructive Command Blocker Hook

A Claude Code `pre-tool-use` hook that blocks dangerous bash commands before execution.

## What It Blocks

| Pattern | Description |
|---------|-------------|
| `rm -rf` / `rm -fr` | Recursive force delete |
| `DROP TABLE` | Destructive SQL |
| `git push --force` / `-f` | Force push |
| `TRUNCATE TABLE` | Destructive SQL |
| `DELETE FROM` (no WHERE) | Mass delete without condition |

## Installation

```bash
curl -o ~/.claude/hooks/hook.py https://raw.githubusercontent.com/dongpod7777-gif/claude-builders-bounty/main/hook.py
chmod +x ~/.claude/hooks/hook.py
```

## How It Works

1. Intercepts all `Bash` tool calls before execution
2. Regex-matches against blocked patterns
3. Logs blocked attempts to `~/.claude/hooks/blocked.log`
4. Returns a block decision with clear reason

## Log Format

```
[2026-06-26T12:00:00] BLOCKED: rm -rf (recursive force delete)
  Command: rm -rf /important/dir
  Project: /home/user/project
```

## Testing

```bash
echo '{"tool_name":"Bash","command":"rm -rf /tmp/test"}' | python3 hook.py
```

Expected output:
```json
{"decision": "block", "reason": "Blocked by destructive-command-hook: rm -rf (recursive force delete)"}
```

## License

MIT
