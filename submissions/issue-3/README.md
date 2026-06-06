# Pre-Tool-Use Safety Hook for Claude Code

A Claude Code `pre-tool-use` hook that intercepts and blocks destructive bash commands before execution.

## Quick Install

```bash
# 1. Install the hook script
cp pre-tool-use-blocker.py ~/.claude/hooks/pre-tool-use-blocker.py && chmod +x ~/.claude/hooks/pre-tool-use-blocker.py

# 2. Register in Claude Code settings
echo '{"hooks":{"preToolUse":[{"matcher":"bash|run|shell|exec","command":"python3 ~/.claude/hooks/pre-tool-use-blocker.py"}]}}' >> ~/.claude/settings.json
```

Done. Restart Claude Code and destructive commands are blocked.

## What It Blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm --recursive` | Irreversible mass deletion |
| `DROP TABLE` / `DROP DATABASE` | Database destruction |
| `git push --force` / `git push -f` | Overwrites remote history |
| `TRUNCATE TABLE` | Empties table without undo |
| `DELETE FROM` without WHERE | Accidentally deletes all rows |
| `:(){ :|:& };:` | Fork bomb 鈥?crashes the system |
| `chmod 777` | World-writable 鈥?security risk |
| `> /dev/sda` / `dd ... of=/dev/sd*` | Raw disk overwrite |
| `mkfs.* /dev/` | Filesystem format |

## How It Works

1. Claude Code calls the hook before executing any `bash`/`run`/`shell`/`exec` tool
2. The hook receives the command via stdin (JSON)
3. It checks against 13 dangerous regex patterns
4. If matched 鈫?blocked with a clear explanation, logged to `~/.claude/hooks/blocked.log`
5. If safe 鈫?allowed through

### Log Format

Each blocked attempt is appended as a JSON line:

```json
{"timestamp": "2026-06-06T14:30:00+00:00", "attempted_command": "rm -rf /tmp/*", "project_path": "/home/user/my-project", "reason": "rm -rf (recursive force remove)"}
```

## Requirements

- Python 3.7+
- No external dependencies (stdlib only)

## Testing

```bash
# Should be blocked:
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /tmp/test"},"cwd":"/test"}' | python3 pre-tool-use-blocker.py

# Should be allowed:
echo '{"tool_name":"bash","tool_input":{"command":"ls -la"},"cwd":"/test"}' | python3 pre-tool-use-blocker.py
```

## License

MIT
