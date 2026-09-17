# Safe Bash Execution Hook for Claude Code

This `pre-tool-use` hook intercepts and blocks dangerous commands (e.g., `rm -rf`, `DROP TABLE`, `git push --force`) before Claude Code can execute them.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use.py ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## Features
- Analyzes commands destined for the `BashCommand` tool
- Blocks `rm -rf`, `DROP TABLE`, `TRUNCATE`, `git push --force`, and `DELETE FROM` without a `WHERE` clause
- Logs all blocked attempts silently to `~/.claude/hooks/blocked.log` with a timestamp and working directory
- Returns a clear error string to Claude so it knows *why* the command failed
