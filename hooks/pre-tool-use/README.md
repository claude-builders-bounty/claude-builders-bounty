# Destructive Command Guard

A Claude Code **pre-tool-use hook** that intercepts dangerous bash commands before they execute.

## Blocked Commands

| Pattern | Why it's blocked |
|---------|-----------------|
| `rm -rf /path` | Recursive force delete — irreversible |
| `DROP TABLE name` | Destroys database table permanently |
| `git push --force` (any variant) | Overwrites remote history |
| `TRUNCATE [TABLE] name` | Removes all rows from table |
| `DELETE FROM table` (no `WHERE`) | Deletes all rows by accident |

Every blocked attempt is logged with timestamp, command, and project path.

## Install

```bash
cp hooks/pre-tool-use/pre_tool_use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre_tool_use.py
```

Then add to your `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use.py"
          }
        ]
      }
    ]
  }
}
```

## Logs

Blocked attempts are written to `~/.claude/hooks/blocked.log`:

```
[2026-06-01 15:30:00 UTC] project=/home/user/project  command=rm -rf build/
[2026-06-01 15:31:00 UTC] project=/home/user/project  command=DROP TABLE users
```
