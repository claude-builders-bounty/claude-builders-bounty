# Pre-Tool-Use Safety Hook

Blocks destructive bash commands (rm -rf, DROP TABLE, git push --force, etc.) before execution.

## Installation

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use
```

That's it. The hook runs automatically on every Bash tool call.

## What It Blocks

- `rm -rf` — recursive forced deletion
- `DROP TABLE` — destructive database operation
- `git push --force` — force push
- `TRUNCATE` — destructive database operation
- `DELETE FROM` without `WHERE` clause

Blocked attempts are logged to `~/.claude/hooks/blocked.log`.
