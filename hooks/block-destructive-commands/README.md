# block-destructive-commands

A Claude Code `pre-tool-use` hook that blocks dangerous bash commands before execution.

## Installation

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use.sh ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## What's Blocked

| Pattern | Reason |
|---------|--------|
| `rm -rf`, `rm -f`, `rm -r` | Destructive deletion |
| `git push --force`, `git push -f` | Force push to remote |
| `DROP TABLE`, `DROP DATABASE` | Schema destruction |
| `TRUNCATE` | Table truncation |
| `DELETE FROM` (no WHERE) | Mass deletion |
| `>: /dev/*` | Device writes |
| `chmod -R 000` | Permission lockout |
| `sudo rm` | Privileged deletion |
| `mkfs.*` | Filesystem format |

Blocked commands are logged to `~/.claude/hooks/blocked.log` with timestamp.
