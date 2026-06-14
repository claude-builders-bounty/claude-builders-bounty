# Safe Bash Hook — pre-tool-use

A [Claude Code](https://docs.anthropic.com/claude-code/hooks) hook that blocks
destructive bash commands before they are executed.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Pattern | Danger |
|---------|--------|
| `rm -rf` | Recursive force delete — can erase entire filesystems |
| `DROP TABLE` | Destructive SQL — deletes a table |
| `git push --force` | Force push — rewrites remote history |
| `TRUNCATE` | Destructive SQL — empties a table |
| `DELETE FROM` without `WHERE` | Unsafe SQL — deletes all rows |

## What Happens When Blocked

1. Claude sees a clear `[[BLOCKED]]` message explaining why
2. The attempt is logged to `~/.claude/hooks/blocked.log` with timestamp + command + project path
3. Safe commands pass through without interference

## Log File

Blocked attempts are recorded in `~/.claude/hooks/blocked.log`:

```
[2026-06-14 22:30:00] BLOCKED: `rm -rf`: recursive force delete
  Command: rm -rf /var/log/app/database.db
  Cwd:     /home/user/projects/myapp
------------------------------------------------------------------------
```

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
```
