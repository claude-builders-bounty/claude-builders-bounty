# Destructive Command Blocker Hook

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before execution.

## Installation

```bash
# 1. Copy the hook into place
cp hooks/pre_tool_use.py ~/.claude/hooks/

# 2. Make it executable
chmod +x ~/.claude/hooks/pre_tool_use.py
```

Then add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "pre_tool_use": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use.py"}]
      }
    ]
  }
}
```

## What it Blocks

| Pattern | Why it's dangerous |
|---------|-------------------|
| Recursive force delete | Irreversible file deletion |
| DROP TABLE | Deletes entire table including all data |
| Git force push to main/master | Overwrites remote branch history |
| TRUNCATE | Deletes all rows without rollback capability |
| DELETE FROM without WHERE | Deletes every row in the table |
| DROP DATABASE | Destroys entire database |
| World-writable chmod | Security vulnerability |
| Raw disk operations (dd) | Can overwrite disks |
| System crash patterns | Process explosion attacks |

## Logging

Every blocked attempt is logged as JSON to `~/.claude/hooks/blocked.log`:
```json
{"timestamp": "2025-01-15T10:30:00Z", "command": "<blocked command>", "project_path": "/home/user/project"}
```

## License

MIT
