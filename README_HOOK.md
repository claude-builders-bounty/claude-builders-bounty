# pre-tool-use — Block Destructive Bash Commands

A Claude Code pre-tool-use hook that prevents accidental execution of dangerous shell commands.

## Installation

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Pattern | Example |
|---------|---------|
| Recursive delete | `rm -rf /`, `rm -fr *` |
| Database destroy | `DROP TABLE`, `DROP DATABASE` |
| Unconditional delete | `DELETE FROM users` (without WHERE) |
| Force push | `git push --force`, `git push -f` |
| Hard reset | `git reset --hard` |
| Raw disk ops | `dd`, `mkfs`, `parted` |
| SUID abuse | `chmod 4777` |
| Pipe-from-internet | `curl ... | bash` |

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Blocked command
- Block reason
- Project directory
