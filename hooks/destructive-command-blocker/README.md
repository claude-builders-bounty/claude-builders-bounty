# 🛡️ Claude Code Destructive Command Blocker

A pre-tool-use hook for Claude Code that intercepts and blocks dangerous
bash commands before they execute.

## Quick Install (2 commands)

```bash
cp pre-tool-use.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use.py
echo '{"hooks":{"PreToolUse":[{"matcher":"","command":"~/.claude/hooks/pre-tool-use.py"}]}}' > ~/.claude/hooks/config.json
```

## Blocked Patterns (18 rules)

| Category | Patterns blocked |
|----------|-----------------|
| Filesystem | `rm -rf`, raw block device writes |
| Database | `DROP TABLE`, `TRUNCATE`, `DELETE FROM` without WHERE |
| Git | `push --force`, `push --delete`, `--force-with-lease` |
| Permissions | `chmod 777`, `chmod -R 777`, `chown -R` |
| Injection | `curl pipe shell`, `wget pipe bash`, `eval` |
| DoS | Fork bombs |

## How It Works

Claude Code calls the hook before every bash command. The hook parses the
command, checks it against 18 regex patterns, and either allows or blocks it.

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp,
full command, and project path.

## Testing

```bash
# Should BLOCK:
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /tmp/test"},"cwd":"."}' | python3 pre-tool-use.py

# Should ALLOW:
echo '{"tool_name":"bash","tool_input":{"command":"ls -la"},"cwd":"."}' | python3 pre-tool-use.py
```

## Requirements

- Python 3.8+
- Claude Code (any version with hooks support)
