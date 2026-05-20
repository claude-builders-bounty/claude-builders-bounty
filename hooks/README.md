# 🛡️ Pre-Tool-Use Destructive Command Guard

A Claude Code hook that intercepts and blocks destructive bash commands before execution.

## Installation (2 commands)

```bash
cp hooks/pre-tool-use-guard.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use-guard.py
```

## What it blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /`, `rm -rf ./*` |
| `DROP TABLE` | `DROP TABLE users;` |
| `DROP DATABASE` | `DROP DATABASE prod;` |
| `TRUNCATE` | `TRUNCATE TABLE logs;` |
| `DELETE FROM` without WHERE | `DELETE FROM users;` |
| `git push --force` | `git push origin main --force` |
| Fork bombs | `:(){ :|:& };:` |
| `mkfs.*` | `mkfs.ext4 /dev/sda` |
| `dd` to device | `dd if=image of=/dev/sda` |
| `chmod 777` on root | `chmod -R 777 /` |

## Blocked attempts log

All blocked commands are logged to `~/.claude/hooks/blocked.log`:
```
[2026-05-20T15:30:00] PROJECT=/home/user/myapp REASON=rm -rf (recursive force remove) COMMAND=rm -rf node_modules/
```

## How it works

The hook reads the tool call from stdin (JSON), checks the `command` field against destructive patterns, and either allows (`{"continue": true}`) or blocks (`{"continue": false}`) the execution.

## Requirements

- Python 3.8+
- Claude Code (hooks directory: `~/.claude/hooks/`)
