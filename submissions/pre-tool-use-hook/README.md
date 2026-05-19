# Pre-Tool-Use Safety Hook

Intercepts dangerous bash commands before Claude Code executes them.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp pre_tool_use.py ~/.claude/hooks/pre_tool_use && chmod +x ~/.claude/hooks/pre_tool_use
```

Then add to `~/.claude/settings.json`:
```json
{"hooks": {"PreToolUse": [{"command": "~/.claude/hooks/pre_tool_use"}]}}
```

## Blocked Commands

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /tmp/cache` |
| `DROP TABLE` | `DROP TABLE users;` |
| `git push --force` | `git push -f origin main` |
| `TRUNCATE` | `TRUNCATE TABLE logs;` |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` |
| `chmod 777` | `chmod -R 777 /var/www` |
| `dd` to device | `dd if=image of=/dev/sda` |

**Safe commands pass through normally** — `ls`, `git commit`, `npm install`, `DELETE FROM ... WHERE id=5`, etc.

## How It Works

1. Hook receives tool call from Claude Code via stdin JSON
2. Only intercepts bash/terminal commands
3. Pattern-matches against known destructive patterns
4. If blocked:
   - Logs to `~/.claude/hooks/blocked.log` with timestamp, command, project path
   - Returns clear reason to Claude
   - Exits with code 1
5. If safe: passes through (exit 0)

## Log Format

```
[2026-05-19T09:45:00Z] BLOCKED | project=/app | reason=DROP TABLE | command=psql -c "DROP TABLE users;"
```

## Requirements

- Python 3.8+
- Claude Code with hooks enabled
