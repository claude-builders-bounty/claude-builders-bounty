# Destructive Command Block Hook

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous bash commands.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block_destructive.py
```

## Features

- **Automatic Interception**: Blocks dangerous patterns in `Bash` and `run_shell_command` tool calls.
- **Safety First**: Prevents `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause.
- **Audit Logging**: Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with a timestamp, the command, and the project path.
- **Clear Feedback**: Returns a JSON response to Claude Code explaining why the command was blocked.

## Requirements

- Python 3.x
- Claude Code
