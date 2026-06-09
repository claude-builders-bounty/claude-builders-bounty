# Dangerous Command Hook

A Claude Code `pre-tool-use` hook that blocks destructive bash commands before execution.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp dangerous-command-hook.py ~/.claude/hooks/pre-tool-use.py
```

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force deletion |
| `DROP TABLE` | Destructive SQL |
| `git push --force` | Force push to remote |
| `TRUNCATE` | Destructive SQL |
| `DELETE FROM` (no WHERE) | Destructive SQL without filter |

## How It Works

1. Intercepts every bash command before execution
2. Checks against destructive patterns using regex
3. Blocks matching commands and explains why
4. Logs all blocked attempts to `~/.claude/hooks/blocked.log`

## Log Format

```
[2026-06-09T12:00:00Z] BLOCKED: rm -rf /tmp/*
  Reason: rm -rf detected: recursive force deletion
  Project: /home/user/my-project
```