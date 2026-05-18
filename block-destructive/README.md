# block-destructive

Claude Code pre-tool-use hook that blocks destructive bash commands.

## Installation (2 commands)

```bash
# 1. Create hooks directory and copy the script
mkdir -p ~/.claude/hooks && cp block-destructive.py ~/.claude/hooks/

# 2. Make it executable
chmod +x ~/.claude/hooks/block-destructive.py
```

> **Note:** The script file name **must** match the hook name. Keep it as `block-destructive.py`.

## What It Blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` / `rm -f` | `rm -rf /var/log/` |
| `DROP TABLE` | `DROP TABLE users;` |
| `git push --force` | `git push origin main --force` |
| `TRUNCATE` | `TRUNCATE TABLE orders;` |
| `DELETE FROM` **without** `WHERE` | `DELETE FROM users;` (safe with `WHERE`) |
| Write to system paths | `> /etc/config` |

## Logs

Blocked commands are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-14 12:30:00] BLOCKED | reason=Matched pattern: rm -rf | cwd=/home/user/project | cmd=rm -rf node_modules
```

## How It Works

- Hook receives the command as JSON via stdin
- Checks against predefined destructive patterns
- If matched: logs the attempt, prints a block response, exits with error
- If safe: exits cleanly (command proceeds)

## Requirements

- Python 3.6+
- Claude Code (hooks feature)
