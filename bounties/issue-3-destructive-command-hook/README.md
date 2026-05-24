# Pre-Tool-Use Hook: Block Destructive Bash Commands

Claude Code hook that intercepts dangerous bash commands and blocks them before execution.

## Install in 2 Commands

```bash
# Step 1: Copy the hook script
mkdir -p ~/.claude/hooks && cp block-destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.py

# Step 2: Add the hook config
#   Copy hooks.json into your project at .claude/hooks/hooks.json
#   OR merge the "PreToolUse" block into your existing ~/.claude/hooks/hooks.json
```

## What It Blocks

| Pattern | Behavior | Example |
|---------|----------|---------|
| `rm -rf /` or system paths | ❌ Blocked | `rm -rf /`, `rm -rf /etc/passwd` |
| `rm -rf` on build dirs | ✅ Allowed (build cleanup) | `rm -rf node_modules dist .next` |
| `DROP TABLE` | ❌ Blocked | Any DDL that drops a table |
| `git push --force` | ❌ Blocked (use `--force-with-lease`) | Pushing with `--force` flag |
| `TRUNCATE TABLE` | ❌ Blocked | Erases all rows from a table |
| `DELETE FROM` without `WHERE` | ❌ Blocked | Mass deletion without filter |
| `DELETE FROM ... WHERE ...` | ✅ Allowed | Safe conditional deletion |

## Logging

Blocked attempts are logged to:

```
~/.claude/hooks/blocked.log
```

Format: `[timestamp] project=/path command='...' reason=...`

## How It Works

1. Fires **before every Bash tool call** in Claude Code
2. Inspects the command against destructive patterns
3. Smart detection: `rm -rf node_modules` is allowed, `rm -rf /etc` is blocked
4. Logs every blocked attempt with timestamp, project path, and command
5. Returns a clear message to Claude explaining why it was blocked
