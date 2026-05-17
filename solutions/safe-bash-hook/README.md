# Claude Code Safe Bash Hook

A `pre-tool-use` hook for Claude Code that automatically intercepts and blocks dangerous destructive commands before they can be executed by the agent.

## Features
- Blocks `rm -rf`, `git push --force`, `DROP TABLE`, `TRUNCATE`, and `DELETE FROM` without `WHERE`.
- Logs all blocked attempts silently to `~/.claude/hooks/blocked.log` with timestamps and execution paths.
- Provides immediate explanatory feedback to Claude Code so it knows *why* the command failed and can try a safer alternative.

## Installation (2 commands)

Just copy the hook into your Claude config directory and make it executable:

```bash
mkdir -p ~/.claude/hooks
curl -sL "https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/solutions/safe-bash-hook/pre-tool-use.py" > ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

*(Note: Claude Code will automatically detect and run the executable file named `pre-tool-use`.)*