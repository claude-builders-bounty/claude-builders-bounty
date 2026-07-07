# Destructive Command Guard

A Claude Code pre-tool-use hook that intercepts and blocks dangerous bash commands before they execute.

## Installation

```bash
mkdir -p ~/.claude/hooks
ln -sf "$PWD/block-destructive.sh" ~/.claude/hooks/pre-tool-use
```

That's it. The hook activates automatically on the next Claude Code session.

## What It Blocks

| Pattern | Risk |
|---------|------|
| `rm -rf`, `rm -rf /` | Irreversible file deletion |
| `DROP TABLE`, `DROP DATABASE` | Database destruction |
| `TRUNCATE TABLE` | Mass data deletion |
| `DELETE FROM` without `WHERE` | Unqualified row deletion |
| `git push --force`, `git push -f` | Force push (history rewrite) |

## What It Logs

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Attempted command
- Project path

## Testing

```bash
echo "rm -rf /important/data" | bash block-destructive.sh
# → ⛛ BLOCKED message

echo "ls -la" | bash block-destructive.sh
# → ls -la (passes through)
```
