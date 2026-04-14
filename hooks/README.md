# Pre-Tool-Use Hook — Destructive Command Blocker

## What It Does

Intercepts dangerous bash/SQL commands in Claude Code before they execute, blocks them, and logs the attempt.

## Files

- `pre_tool_use.py` — Python implementation (recommended: cross-platform)
- `pre_tool_use.js` — JavaScript/Node.js implementation

## Installation

### Python hook

```bash
chmod +x pre_tool_use.py
```

In your Claude Code `settings.json`:

```json
{
  "hooks": {
    "preToolUse": ["python3", "/absolute/path/to/pre_tool_use.py"]
  }
}
```

### JavaScript hook

```json
{
  "hooks": {
    "preToolUse": "/absolute/path/to/pre_tool_use.js"
  }
}
```

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf .` | Recursive rm on current directory |
| `DROP TABLE` | Direct table deletion |
| `TRUNCATE TABLE` | Full table wipe |
| `DELETE FROM <table>;` | DELETE without WHERE clause |
| `git push --force` | History rewrite |
| `git push -f` | History rewrite |
| `DROP DATABASE` | Complete database deletion |

## Log

All blocked commands → `~/.claude/hooks/blocked.log`:

```
[2026-04-14T01:00:00.000Z] BLOCKED tool=Bash reason=DROP TABLE
  command="DROP TABLE users;"
  cwd=/path/to/project
```

## Testing

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"ls"},"context":{}}' | python3 pre_tool_use.py
# {"decision": "allow"}

echo '{"tool_name":"Bash","tool_input":{"command":"DROP TABLE users;"},"context":{}}' | python3 pre_tool_use.py
# {"decision": "block", "reason": "DESTRUCTIVE_COMMAND: DROP TABLE — data destruction", ...}
```
