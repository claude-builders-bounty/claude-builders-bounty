# Claude Code Pre-Tool-Use Hook: Block Destructive Commands

A safety hook for [Claude Code](https://docs.anthropic.com/claude-code) that intercepts and blocks dangerous bash commands before they execute.

## Install (2 commands)

```bash
# 1. Copy the hook into your Claude Code hooks directory
ln -sf "$(pwd)/pre-tool-use-destructive-hook.py" ~/.claude/hooks/pre-tool-use-destructive-hook.py

# 2. Create the log file (must exist for the hook to append)
touch ~/.claude/hooks/blocked.log
```

## Usage

Claude Code will automatically invoke the hook before every bash command. If a dangerous pattern is detected, the tool call is blocked and an explanation is printed.

## Blocked Patterns

| Pattern | Blocks |
|---|---|
| `rm -rf /` | Root filesystem deletion |
| `rm -rf *` | Recursive delete from current dir |
| `DROP TABLE` | SQL drop without WHERE |
| `TRUNCATE TABLE` | SQL truncate |
| `git push --force` / `-f` | Force-push rewrites history |
| `DELETE FROM` without WHERE | Unconditional row deletion |
| `chmod -R 777` | World-writable permissions |
| `:(){ :|:& };:` | Fork bomb |

## Log

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with:

```
[2026-04-01T00:00:00+00:00] BLOCKED | project: /path/to/project | reason: DROP TABLE without WHERE | command: DROP TABLE users;
```

## Disable Temporarily

```bash
mv ~/.claude/hooks/pre-tool-use-destructive-hook.py ~/.claude/hooks/pre-tool-use-destructive-hook.py.disabled
```

## Files

- `pre-tool-use-destructive-hook.py` — the hook script (Python 3)
- `README.md` — this file
