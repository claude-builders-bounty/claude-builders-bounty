# 🛡 Bash Guard — Claude Code Safety Hook

Pre-tool-use hook that blocks dangerous bash commands before execution.

## Install (1 command)

```bash
cp pre-tool-use ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## What it blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /important/dir` |
| `DROP TABLE` | `DROP TABLE users` |
| `TRUNCATE` | `TRUNCATE logs` |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` |
| `git push --force` | `git push origin main --force` |
| `chmod 777` | `chmod 777 /etc/passwd` |
| Direct disk writes | `dd if=x of=/dev/sda` |

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## Requirements

- Python 3.8+
- Claude Code
