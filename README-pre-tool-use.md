# Pre-Tool-Use Hook — Dangerous Command Blocker

A [Claude Code hook](https://docs.anthropic.com/claude-code/hooks) that intercepts and blocks destructive bash commands before they execute.

**Bounty**: [$100 — Issue #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

## Installation

```bash
# 1. Copy the hook
mkdir -p ~/.claude/hooks/
cp hooks/pre-tool-use ~/.claude/hooks/

# 2. Make it executable
chmod +x ~/.claude/hooks/pre-tool-use
```

That's it. Claude Code will now block dangerous commands automatically.

## What It Blocks

| Pattern | Why |
|---|---|
| `rm -rf` | Destructive recursive delete — accidental data loss |
| `git push --force` | Overwrites remote history — use `--force-with-lease` instead |
| `DROP TABLE` | Permanently deletes a database table |
| `TRUNCATE` | Quickly deletes all rows (irreversible without backup) |
| `DELETE FROM` without `WHERE` | Would delete all rows |
| `UPDATE ... SET` without `WHERE` | Would modify all rows |

## Logs

All blocked commands are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Attempted command
- Project path
- Reason

## How It Works

Claude Code calls the `pre-tool-use` hook before every bash command. The hook:
1. Reads the command from stdin (JSON)
2. Checks against known dangerous patterns
3. Returns exit code `1` (block) with a clear message, or `0` (allow)
4. Logs all blocked attempts

Safe commands pass through without interference.
