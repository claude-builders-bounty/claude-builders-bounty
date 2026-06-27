# Pre-Tool-Use Safety Hook for Claude Code

Blocks destructive bash commands before they execute.

## Installation

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre-tool-use https://raw.githubusercontent.com/Dizzztroyer/claude-builders-bounty/main/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Irreversible deletion — use a trash dir or explicit paths |
| `git push --force` | Destroys remote history — use `--force-with-lease` |
| `DROP TABLE` | Irreversible schema change — use migrations |
| `TRUNCATE` | Wraps DROP+CREATE — use `DELETE` |
| `DELETE FROM` without `WHERE` | Wipes entire table |

Blocked commands are logged to `~/.claude/hooks/blocked.log` with timestamp, project path, and the attempted command.
