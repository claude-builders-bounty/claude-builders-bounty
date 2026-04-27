# 🛡️ Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that intercepts and blocks destructive bash commands before they execute.

## Installation

```bash
mkdir -p ~/.claude/hooks && curl -sL https://raw.githubusercontent.com/haoyousun60-create/claude-builders-bounty/main/hooks/pre-tool-use.py -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

That's it! Claude Code will automatically discover the hook and apply it.

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` / `rm --recursive` | Unconditional recursive delete |
| `DROP TABLE` | Destructive database operation |
| `git push --force` | Force-push (overwrites history) |
| `TRUNCATE` | Destructive database operation |
| `DELETE FROM` **without** `WHERE` | Accidental data wipe |

## What It Logs

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-04-27 14:30:00] BLOCKED
  Reason:  Unconditional recursive delete
  Command: rm -rf /project/data
  Project: /Users/me/my-project
```

## Safe Bypasses

The following patterns are automatically allowed (they're common maintenance tasks):
- `rm -rf /tmp/*` — clearing temp files
- `rm -rf node_modules` — package management
- `rm -rf .git/*` — git operations (rare but legit)

## Requirements

- Python 3.6+ (pre-installed on macOS/Linux)
- Claude Code (with hook support)

## License

MIT
