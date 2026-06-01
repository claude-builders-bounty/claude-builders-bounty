# Destructive Command Hook for Claude Code

Pre-tool-use hook that intercepts dangerous bash commands before execution.

## Blocked Patterns

| Pattern | Examples Blocked |
|---------|-----------------|
| `rm -rf` | `rm -rf /`, `rm -rf node_modules` |
| `DROP TABLE/DATABASE` | `DROP TABLE users`, `DROP DATABASE prod` |
| `git push --force` | `git push --force origin main` |
| `TRUNCATE` | `TRUNCATE TABLE logs` |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` |
| `chmod 777` | `chmod -R 777 .` |
| Fork bombs, dd to /dev, mkfs |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use/pre_tool_use.py ~/.claude/hooks/
```

## Blocked Attempt Log

Every blocked command is logged to `~/.claude/hooks/blocked.log`:

```json
{"timestamp":"2026-06-01T12:00:00Z","command":"rm -rf /","reason":"recursive force delete","project":"/home/user/myapp"}
```
