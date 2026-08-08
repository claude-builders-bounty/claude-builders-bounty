# Destructive Command Blocker Hook

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous commands before they execute.

## Features
- Intercepts destructive patterns: `rm -rf`, `git push --force`, `DROP TABLE`, `TRUNCATE`, and `DELETE FROM` (without a `WHERE` clause).
- Logs blocked attempts to `~/.claude/hooks/blocked.log` (includes timestamp, project path, and attempted command).
- Safely halts execution and provides a clear rejection message directly to Claude.

## Installation

Install this hook in 2 commands or fewer:

```bash
mkdir -p ~/.claude/hooks
cp pre_tool_use.py ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh
```

*(Note: Claude Code expects the file to be named `pre-tool-use.sh` or similar executable in the hooks directory. Since python is cross-platform and handles regex well, we just map the python script as the executable hook).*

## How it works
When Claude attempts to run a bash tool, this script intercepts the JSON payload sent via `stdin`. It scans the command string for known destructive patterns. If a match is found, it logs the event, prints a JSON error message, and exits with status code `1`, which stops Claude from running the command. Harmless commands pass through with status `0`.
