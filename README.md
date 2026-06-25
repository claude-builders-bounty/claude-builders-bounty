# Destructive Command Hook for Claude Code

A pre-tool-use hook that blocks dangerous bash commands before they execute.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/destructive_command_hook.py ~/.claude/hooks/
```

## What It Blocks

- rm -rf / - Recursive force delete
- DROP TABLE - Database table deletion
- git push --force - Force push to remote
- TRUNCATE - Table truncation
- DELETE FROM without WHERE - Mass deletion

## How It Works

1. Intercepts bash commands before execution
2. Checks against destructive patterns
3. Blocks dangerous commands with clear explanation
4. Logs all blocked attempts to ~/.claude/hooks/blocked.log
5. Allows normal commands to pass through

## Log File

Blocked commands are logged with timestamp, command, and project path.
