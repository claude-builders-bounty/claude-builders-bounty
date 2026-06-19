# Destructive Bash Blocker Hook

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous commands before they are executed.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use.py ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## Features
- Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without `WHERE`.
- Logs all blocked commands to `~/.claude/hooks/blocked.log` with timestamp, project path, and attempted input.
- Exits with a clear explanation message sent back to Claude when a command is blocked.
- Clean pass-through for safe commands.
