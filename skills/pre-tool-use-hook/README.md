# Pre-tool-use Hook — Security Guard for Claude Code

Blocks destructive bash commands before they execute. Protects against accidental `rm -rf`, `DROP TABLE`, `git push --force`, and more.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use-hook.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use-hook.py
```

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf /` | Full system wipe |
| `rm -rf $` | Variable expansion wipe |
| `DROP TABLE` | Database destruction |
| `TRUNCATE TABLE` | Database destruction |
| `git push --force` | History rewrite |
| `DELETE FROM` without WHERE | Data loss risk |

## Log Location

All blocked attempts are logged to: `~/.claude/hooks/blocked.log`

Format: `[ISO timestamp] Blocked: <command> | Project: <path>`

## For Claude Code Hook Integration

Place at `~/.claude/hooks/pre-tool-use-hook.py` and invoke from your hook configuration. The hook reads JSON input from Claude Code's hook protocol.
