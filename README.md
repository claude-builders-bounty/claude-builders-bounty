# Destructive Command Guard — Claude Code Pre-Tool-Use Hook

Blocks dangerous bash commands before Claude Code executes them.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use ~/.claude/hooks && chmod +x ~/.claude/hooks/pre-tool-use
```

Or install from this repo:

```bash
curl -fsSL https://raw.githubusercontent.com/18060910075zx-coder/claude-builders-bounty/destructive-guard/pre-tool-use -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## What it blocks

| Pattern | Example blocked commands |
|---------|-------------------------|
| `rm -rf` | `rm -rf /tmp/build`, `rm -fr node_modules` |
| `DROP TABLE` | `DROP TABLE users`, `DROP DATABASE prod` |
| `TRUNCATE` | `TRUNCATE logs`, `TRUNCATE TABLE sessions` |
| `git push --force` | `git push --force origin main`, `git push -f` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users` |

## What it DOESN'T block

- `rm file.txt` (single file, no force flag)
- `DELETE FROM users WHERE id = 42` (has WHERE clause)
- `git push origin main` (no force flag)
- `SELECT`, `INSERT`, `UPDATE` statements
- All non-Bash tools (Read, Write, Grep, etc.)

## Logs

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```json
{"timestamp": "2026-05-19T15:30:00Z", "command": "rm -rf node_modules", "reason": "rm -rf — Recursive force removal...", "cwd": "/home/user/project"}
```

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
```

## How it works

Claude Code fires a pre-tool-use event before every Bash command. This hook:
1. Reads the event from stdin
2. Checks if the tool is `Bash`
3. Normalizes the command (strips comments, collapses whitespace)
4. Checks against 5 dangerous patterns (case-insensitive)
5. If dangerous → logs to `blocked.log`, returns exit code 2 (block)
6. If safe → returns exit code 0 (allow)

---

Part of the [Claude Builders Bounty](https://github.com/claude-builders-bounty) program · Issue #3
