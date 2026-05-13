# Claude Code Destructive Command Blocker

A `pre-tool-use` hook for Claude Code that intercepts dangerous bash commands before execution.

## Blocked Patterns

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /` | Recursive force deletion can destroy entire directory trees |
| `DROP TABLE` | `DROP TABLE users;` | Irreversible data loss |
| `git push --force` | `git push --force origin main` | Rewrites remote history, can destroy teammates' work |
| `TRUNCATE` | `TRUNCATE TABLE orders;` | Removes all rows without individual deletion logging |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Deletes every row in the table |

## Install

```bash
cp hooks/block-destructive.sh ~/.claude/hooks/block-destructive.sh && chmod +x ~/.claude/hooks/block-destructive.sh
```

Then add the hook to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "hook": "~/.claude/hooks/block-destructive.sh"
      }
    ]
  }
}
```

## How It Works

1. Claude Code triggers the hook before every `Bash` tool call
2. The hook reads the JSON payload from stdin (contains `tool_name`, `tool_input`, `project_path`)
3. If the command matches a destructive pattern, the hook:
   - Logs the attempt to `~/.claude/hooks/blocked.log` with timestamp, command, and project path
   - Returns an error message explaining why the command was blocked
   - Exits with code 2 (tells Claude Code to reject the tool call)
4. Safe commands pass through with exit code 0

## Log Format

Every blocked attempt is appended to `~/.claude/hooks/blocked.log`:

```
[2026-05-13T10:30:00Z] BLOCKED (rm -rf) | project=/home/user/myapp | command=rm -rf node_modules /
[2026-05-13T10:31:00Z] BLOCKED (DROP TABLE) | project=/home/user/myapp | command=psql -c "DROP TABLE users"
```

## Safe Commands That Pass Through

- `rm file.txt` — no `-rf` flags
- `git push origin main` — no `--force`
- `DELETE FROM users WHERE id = 5;` — has a WHERE clause
- All non-bash tool calls (Read, Write, Edit, etc.)
