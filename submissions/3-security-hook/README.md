# Pre-Tool-Use Security Hook

Blocks destructive bash commands from being executed by Claude Code.

## Quick Start

```bash
# Install
mkdir -p ~/.claude/hooks/pre-tool-use
ln -sf "$PWD/block-destructive.sh" ~/.claude/hooks/pre-tool-use/

# Test
echo "rm -rf /" | bash ~/.claude/hooks/pre-tool-use/block-destructive.sh
# → ⛔ Blocked
```

## Blocked Patterns

| Command | Risk |
|---------|------|
| `rm -rf`, `rm -fr` | Destructive deletion |
| `DROP TABLE`, `DROP DATABASE` | Database destruction |
| `TRUNCATE` | Mass data loss |
| `DELETE FROM` (no WHERE) | Mass deletion |
| `git push --force`, `git push -f` | Force push |
| `mkfs.*` | Filesystem format |
| `chmod -R 0 /` | System lockout |
| `chown -R /` | Ownership corruption |
| Fork bombs | System crash |

## Logging

All blocked attempts are logged to:
```
~/.claude/hooks/pre-tool-use/blocked.log
```

With: timestamp, attempted command, project path.
