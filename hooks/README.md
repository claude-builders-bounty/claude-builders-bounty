# Safe Bash Hook — Pre-Tool-Use Safety for Claude Code

A pre-tool-use hook that blocks dangerous bash commands before they execute.

## What It Blocks

| Pattern | Why | Suggested Alternative |
|---------|-----|----------------------|
| `rm -rf` | Recursive force delete | Use a trash directory or `rm -r` with confirmation |
| `DROP TABLE` | Destructive DB operation | Use `DROP TABLE IF EXISTS` after confirming in a migration |
| `git push --force` | Destructive force push | Use `git push --force-with-lease` instead |
| `TRUNCATE` | Mass data deletion | Use `DELETE FROM` with a WHERE clause |
| `DELETE FROM` (no WHERE) | Unscoped deletion | Always add a WHERE clause to limit scope |

## How It Works

The hook intercepts every `Bash` tool call before execution. If the command matches a dangerous pattern, it:

1. **Blocks** the command with a clear error message
2. **Logs** the attempt to `~/.claude/hooks/blocked.log` with timestamp and reason
3. **Exits** with code 1, preventing execution

Normal commands pass through without any overhead.

## Installation

```bash
# One-line install
cp hooks/pre-tool-use.sh ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

Verify it's working:

```bash
# This should be blocked
echo "Try to rm -rf something" | grep -q "rm -rf" && echo "Would be blocked"

# This should pass normally
ls -la
```

## Logs

Blocked commands are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-07 15:30:00] BLOCKED: rm -rf node_modules
[2026-05-07 15:30:00] Reason: Recursive force delete (rm -rf) is blocked.
```

## Requirements

- **Bash** 4+ (default on macOS and Linux)
- **Python 3** (used for safe JSON parsing of tool input)

## Files

| File | Purpose |
|------|---------|
| `hooks/pre-tool-use.sh` | The hook script — copy to `~/.claude/hooks/pre-tool-use` |
| `hooks/blocked.log` | Blocked command log (created automatically) |
