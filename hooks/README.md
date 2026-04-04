# Destructive Command Blocker Hook

> Pre-tool-use hook for Claude Code that blocks destructive bash commands before execution.

## Install (2 commands)

```bash
# 1. Copy the hook
cp hooks/pre-tool-use-block-destructive.py ~/.claude/hooks/pre-tool-use.py

# 2. Add to your hooks config (~/.claude/hooks.json)
echo '{"hooks":{"PreToolUse":[{"matcher":"Bash","command":"python3 ~/.claude/hooks/pre-tool-use.py"}]}}' > ~/.claude/hooks.json
```

## What It Blocks

| Pattern | Description |
|---------|-------------|
| `rm -rf /path` | Recursive force delete |
| `DROP TABLE/DATABASE` | SQL database destruction |
| `TRUNCATE TABLE` | SQL table truncation |
| `DELETE FROM` | SQL delete operations |
| `git push --force` | Force push to remote |
| `docker system prune` | Docker cleanup |
| `mkfs`, `dd of=/dev/` | Disk formatting/write |
| `shutdown`, `reboot` | System power operations |
| `chmod -R 777 /` | Permission escalation |
| `kubectl delete namespace` | Kubernetes namespace deletion |
| Fork bomb patterns | `:(){:|:&};:` |

## Features

- ✅ **Whitelist** — Safe commands like `rm -rf node_modules` are allowed
- ✅ **Logging** — Every blocked attempt logged to `~/.claude/hooks/blocked.log`
- ✅ **Clear feedback** — Claude gets a message explaining why the command was blocked
- ✅ **Zero interference** — Normal commands pass through untouched

## Log Format

```json
{"timestamp": "2026-04-03T17:45:00Z", "command": "rm -rf /", "reason": "rm -rf with path", "project_path": "/home/user/project"}
```

## Adding Custom Patterns

Edit the `DESTRUCTIVE_PATTERNS` list in the script. Each entry is a `(regex, description)` tuple.

## License

MIT
