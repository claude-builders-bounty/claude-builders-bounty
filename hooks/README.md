# Claude Guard Hook 🛡️

A `pre-tool-use` hook for Claude Code that prevents destructive bash commands from being executed accidentally.

## Features
- Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` (without WHERE).
- Logs all blocked attempts to `~/.claude/hooks/blocked.log`.
- Written in Python for portability and complex pattern matching.

## Installation (2 Commands)
```bash
mkdir -p ~/.claude/hooks && cp tools/claude_guard_hook.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## How it Works
When Claude attempts to run a bash tool, Claude Code triggers the `pre-tool-use` hook. If the command contains any dangerous patterns, the hook prints a security warning and exits with status 1, which tells Claude Code to abort the execution.
