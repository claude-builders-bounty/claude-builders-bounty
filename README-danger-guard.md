# Danger Guard — Claude Code Pre-Tool-Use Hook

Blocks destructive bash commands before execution.

## Install (2 commands)

mkdir -p ~/.claude/hooks
cp danger-guard ~/.claude/hooks/


## Blocked Patterns
- Recursive force delete
- DROP TABLE / TRUNCATE
- DELETE FROM without WHERE clause
- git push --force to main/master
- chmod -R 777 on root

## How It Works
The hook reads the proposed command from stdin, checks against dangerous patterns, and either:
- **Blocks**: logs to blocked.log with timestamp and reason
- **Allows**: passes the command through unchanged
