# Pre-Tool-Use Hook: Block Destructive Bash Commands

Blocks dangerous commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE) in Claude Code.

## Install

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
ln -sf "$PWD/block-destructive.sh" ~/.claude/hooks/pre-tool-use/block-destructive.sh
chmod +x ~/.claude/hooks/pre-tool-use/block-destructive.sh
```

## What it blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /` |
| `DROP TABLE` | `DROP TABLE users;` |
| `git push --force` | `git push --force origin main` |
| `TRUNCATE` | `TRUNCATE payments;` |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` |

Blocked commands are logged to `~/.claude/hooks/blocked.log`.
