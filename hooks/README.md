# 🛡️ Safety Hook for Claude Code

Blocks dangerous bash commands before they execute.

## Installation (2 commands)

```bash
cp safety_hook.py ~/.claude/hooks/
cp hook.sh ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh
```

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive file deletion |
| `DROP TABLE` | Dropping database tables |
| `DELETE FROM` (no WHERE) | Unconditional delete |
| `TRUNCATE TABLE` | Truncating tables |
| `git push --force` | Force push |
| `git reset --hard` | Hard reset |
| `curl \| bash` | Piping to shell |
| `chmod 777` | Overly permissive |

## How It Works

1. Claude Code runs `pre-tool-use.sh` before every Bash command
2. The Python script checks the command against blocked patterns
3. If matched: command is blocked, logged, and Claude sees an error
4. If clean: command proceeds normally

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:
```
[2026-05-10T14:30:00] BLOCKED: Recursive/forced file deletion
  Command: rm -rf /important/data
  Project: /home/user/project
```

## Customization

Edit `BLOCKED_PATTERNS` in `safety_hook.py` to add/remove patterns.
