# Block Destructive Commands Hook

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block-destructive.sh ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Destructive and irreversible file deletion |
| `DROP TABLE` | Permanently deletes database tables |
| `git push --force` | Overwrites remote history |
| `TRUNCATE` | Removes all rows from a table |
| `DELETE FROM` without `WHERE` | Deletes all rows unintentionally |

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (UTC)
- Project path
- Attempted command

## Behavior

- **Blocked commands**: Exit code 1, clear explanation shown to Claude
- **Normal commands**: Pass through unchanged (exit code 0)
- **No interference**: Only blocks explicitly matched destructive patterns
