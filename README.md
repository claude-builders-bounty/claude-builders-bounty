# Pre-Tool-Use Hook — Destructive Command Blocker ($100)

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before execution.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre-tool-use.py https://raw.githubusercontent.com/Arkhos-Overlord/claude-builders-bounty/main/pre-tool-use.py
```

Claude Code auto-discovers hooks in `~/.claude/hooks/`.

## What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /` | Destructive deletion |
| `DROP TABLE` | `DROP TABLE users` | Data loss |
| `DELETE FROM` without WHERE | `DELETE FROM users` | Mass deletion |
| `TRUNCATE` | `TRUNCATE orders` | Table wipe |
| `git push --force` | `git push --force main` | History rewrite |
| `shutdown` / `reboot` | `shutdown -h now` | System interruption |
| `mkfs.` / `dd if=` | `dd if=/dev/zero of=/dev/sda` | Disk destruction |
| Fork bombs | `:(){ :\|:& };:` | System crash |

## How It Works

- Every bash command passes through `pre-tool-use`
- Returns `{"veto": true, "message": "..."}` for blocked commands
- Logs all blocked attempts to `~/.claude/hooks/blocked.log`
- Normal commands pass through unmodified
