# Pre-Tool-Use Security Hook for Claude Code

Blocks dangerous bash commands before they execute, protecting your system from accidental destruction.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block_destructive.py
```

Claude Code auto-detects hooks in `~/.claude/hooks/` and runs them on every `pre-tool-use` event.

## What it blocks

| Category | Examples |
|----------|----------|
| **Destructive** | `rm -rf /`, `mkfs`, `dd if=/dev/zero of=...` |
| **SQL** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` without WHERE |
| **Git** | `git push --force`, `git reset --hard`, `git filter-branch` |
| **Filesystem** | `chmod -R 0`, `shutdown`, `reboot` |

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Attempted command
- Project path
- Blocked category

## How it works

Claude Code sends the proposed command as JSON via stdin. The hook parses it, checks against regex patterns, and returns `{"allow": false}` with a clear reason if the command is dangerous. Safe commands pass through without interference.
