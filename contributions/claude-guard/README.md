# 🛡️ claude-guard — Pre-tool-use Hook

**Bounty**: [#3 $100](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

Blocks dangerous bash commands before they execute in Claude Code.

## Install (2 commands)
```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use.py ~/.claude/hooks/pre-tool-use
```

Done. Restart Claude Code — it's active immediately.

## What It Blocks
| Command | Reason |
|---------|--------|
| `rm -rf` | Permanent file deletion |
| `git push --force` | Destroys remote history |
| `DROP TABLE` | Irreversible data loss |
| `TRUNCATE` | Destroys all rows |
| `DELETE FROM` (no WHERE) | Would delete all rows |
| `sudo rm` | Escalated destruction |
| `dd if=` | Disk overwrite |

## What It Allows
`cp`, `mv`, `rm` (without `-rf`), `git push` (without `--force`), normal dev commands.

## Logging
All blocked attempts logged to `~/.claude/hooks/blocked.log` with timestamp + command + project.
