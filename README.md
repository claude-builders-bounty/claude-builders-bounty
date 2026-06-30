# Pre-Tool-Use Hook: Destructive Bash Command Blocker

A [Claude Code hook](https://docs.anthropic.com/claude-code/hooks) that intercepts and blocks destructive bash commands before they execute.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## What it blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf`, `rm -r`, `rm --recursive` | Recursive force-delete blocked |
| `DROP TABLE` | Destructive schema change blocked |
| `git push --force` | Force-push blocked |
| `TRUNCATE` | Table truncation blocked |
| `DELETE FROM` without `WHERE` clause | Unbounded delete blocked |

## What it logs

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (UTC ISO 8601)
- Reason for blocking
- Project path (current working directory)
- Attempted command

## How it works

The hook receives each tool-use JSON from Claude Code on stdin. It extracts the command field and checks it against a set of destructive patterns. Safe commands exit immediately with code 0. A blocked command writes to the log, prints a clear explanation to stdout, and exits with code 1 to prevent execution.