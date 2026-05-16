# 🛡️ Destructive Command Blocker

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before execution.

## What It Blocks

| Pattern | Example | Status |
|---------|---------|--------|
| `rm -rf` | `rm -rf /tmp` | 🚫 BLOCKED |
| `rm -f` | `rm -f file.txt` | 🚫 BLOCKED |
| `git push --force` | `git push origin main --force` | 🚫 BLOCKED |
| `DROP TABLE` | `DROP TABLE users` | 🚫 BLOCKED |
| `TRUNCATE TABLE` | `TRUNCATE TABLE logs` | 🚫 BLOCKED |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` | 🚫 BLOCKED |
| `DELETE FROM` (with WHERE) | `DELETE FROM users WHERE id=1` | ✅ ALLOWED |
| `rm -f *.log` | `rm -f debug.log` | ✅ ALLOWED |
| Normal commands | `ls`, `cat`, `echo` | ✅ ALLOWED |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre_tool_use.py ~/.claude/hooks/
```

Done. Claude Code now blocks destructive commands automatically.

## How It Works

1. Claude Code sends JSON tool requests to `~/.claude/hooks/pre_tool_use.py` via stdin
2. The hook checks the `Bash` command against destructive patterns
3. If matched, it replaces the command with a safe `echo` that explains the block
4. Every block is logged to `~/.claude/hooks/blocked.log`

## Log Format

```json
{"timestamp": "2025-05-16T09:15:30+00:00", "attempted_command": "rm -rf /tmp/test", "reason": "Destructive pattern matched: rm\\s+(-[a-zA-Z]*f[a-zA-Z]*\\s+|\\s*-\\s*)+.*", "project_path": "/home/devin/project"}
```

## Test

```bash
cd destructive-command-blocker
pytest tests/test_hook.py -v
```

**16 tests, all passing.**

## Temporarily Disable

```bash
mv ~/.claude/hooks/pre_tool_use.py ~/.claude/hooks/pre_tool_use.py.disabled
```

## Why These Rules

- **`rm -rf`** — Irreversible recursive deletion
- **`git push --force`** — Overwrites remote history, breaks collaborators
- **`DROP TABLE`** — Instant data loss, no undo
- **`TRUNCATE`** — Faster than DELETE but equally destructive
- **`DELETE FROM` without WHERE** — Deletes entire table contents accidentally
- **`rm -f *.log`** — Allowed because logs are ephemeral by design

## License

MIT
