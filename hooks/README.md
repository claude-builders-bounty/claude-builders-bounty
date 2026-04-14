# Destructive Command Blocker Hook

A Claude Code `pre-tool-use` hook that blocks dangerous bash commands before execution.

## Blocked Patterns
- `rm -rf` and recursive force deletes
- `DROP TABLE` statements
- `git push --force`
- `TRUNCATE` statements
- `DELETE FROM` without `WHERE` clause

## Installation (2 steps)

```bash
mkdir -p ~/.claude/hooks/
cp hook.py ~/.claude/hooks/pre-tool-use.py
```

## How It Works
The hook intercepts bash commands via stdin JSON, checks against dangerous patterns, and blocks execution (exit 2) if matched. All blocked attempts are logged to `~/.claude/hooks/blocked.log`.

## Log Format
```
[timestamp] BLOCKED: reason | Command: cmd | Project: path
```
