# Destructive Command Blocker Hook

Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands.

## Installation (2 commands)

```bash
cp pre_tool_use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre_tool_use.py
```

Then add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "pre_tool_use": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use.py"}]
    }]
  }
}
```

## What it Blocks

| Pattern | Risk |
|---------|------|
| Recursive force delete | Irreversible file deletion |
| DROP TABLE / DROP DATABASE | Destroys database objects |
| Git force push | Overwrites remote history |
| TRUNCATE | Deletes all rows, no rollback |
| DELETE FROM without WHERE | Deletes every row |
| World-writable chmod | Security vulnerability |

## Logging

Blocked attempts are logged as JSON to `~/.claude/hooks/blocked.log`:
```json
{"timestamp": "2025-01-15T10:30:00Z", "command": "...", "project_path": "/home/user/project"}
```

## License

MIT
