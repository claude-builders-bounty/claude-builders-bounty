# Destructive Command Blocker — Claude Code Hook

## What it does

Intercepts dangerous bash commands before Claude Code executes them. Blocked commands are logged and Claude receives a clear explanation.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "pre-tool-use": [
      { "command": "bash ~/.claude/hooks/block-destructive.sh" }
    ]
  }
}
```

## Blocked patterns

| Pattern | Example | Reason |
|---------|---------|--------|
| `rm -rf` (unsafe targets) | `rm -rf /` | Irreversible recursive delete |
| `DROP TABLE` | `DROP TABLE users` | Destroys table data |
| `TRUNCATE` | `TRUNCATE TABLE sessions` | Deletes all rows |
| `DELETE FROM` without `WHERE` | `DELETE FROM logs` | Deletes all rows |
| `git push --force` to protected branches | `git push --force origin main` | Rewrites shared history |
| Direct disk writes | `dd of=/dev/sda` | Destroys filesystem |
| `chmod 777` on system dirs | `chmod 777 /etc` | Security risk |
| `mkfs` / `FORMAT` | `mkfs.ext4 /dev/sdb1` | Destroys filesystem |

## Safe patterns (not blocked)

- `rm -rf node_modules` — safe cleanup targets are whitelisted
- `rm -rf .next dist build __pycache__ .cache coverage`
- `git push --force` to feature branches (not main/master/prod/release)
- `DELETE FROM logs WHERE created_at < '2024-01-01'` — has WHERE clause

## Log

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-08-19T12:00:00Z] BLOCKED | /home/user/project | rm -rf /tmp/important
```

## How it works

1. Claude Code sends the bash tool input as JSON on stdin
2. The hook extracts the `command` field
3. It checks against dangerous patterns (case-insensitive)
4. If matched: logs to `blocked.log`, outputs `{"decision": "block", "reason": "..."}`, exits with code 2
5. If clean: exits 0, Claude proceeds normally
