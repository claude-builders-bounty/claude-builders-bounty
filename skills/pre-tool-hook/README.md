# Pre-tool-use Hook — Block Destructive Bash Commands

A Claude Code hook that intercepts and blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
# 1. Copy hook to Claude hooks directory
mkdir -p ~/.claude/hooks && cp pre_tool_use_hook.py ~/.claude/hooks/pre-tool-use

# 2. Make executable
chmod +x ~/.claude/hooks/pre-tool-use
```

That's it. The hook activates automatically when using Claude Code.

## What It Blocks

| Pattern | Example | Blocked Reason |
|---------|---------|----------------|
| `rm -rf` | `rm -rf /` | Prevents recursive force deletion |
| `DROP TABLE` | `DROP TABLE users;` | Requires explicit approval |
| `git push --force` | `git push --force origin main` | Prevents history rewrite |
| `TRUNCATE` | `TRUNCATE TABLE logs;` | Requires explicit approval |
| `DELETE FROM` without WHERE | `DELETE FROM users;` | Missing WHERE clause |

All blocked attempts are logged to `~/.claude/hooks/blocked.log`.

## Log Format

```
[2026-03-30T18:55:00Z] command=rm -rf / reason=Blocked: 'rm -rf' is too destructive
[2026-03-30T18:56:00Z] command=git push --force origin main reason=Blocked: 'git push --force' can rewrite history
```

## Hook Behavior

- Claude Code calls the hook before executing any bash command.
- The hook reads a JSON payload from stdin with keys: `tool`, `input`.
- If the command matches a blocked pattern, the hook:
  1. Logs the attempt to `blocked.log`.
  2. Prints a clear reason to stderr.
  3. Exits with non-zero status to block execution.
- All other commands pass through (exit 0).

## Requirements

- Python 3.7+
- Claude Code (v0.6.0+ for hooks support)

## License

MIT
