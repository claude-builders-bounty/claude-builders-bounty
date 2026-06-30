# Destructive Command Block Hook

Blocks dangerous bash commands before Claude Code executes them.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp block_hook.py ~/.claude/hooks/block_hook.py
chmod +x ~/.claude/hooks/block_hook.py
```

## Blocks

| Pattern | Severity |
|---------|----------|
| `rm -rf` | CRITICAL |
| `DROP TABLE` | CRITICAL |
| `git push --force` | HIGH |
| `TRUNCATE` | CRITICAL |
| `DELETE FROM` (no WHERE) | HIGH |

## Logs

All blocked attempts are logged to `~/.claude/hooks/blocked.log`
