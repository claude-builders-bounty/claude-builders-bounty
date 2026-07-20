# Safe Bash Pre-Tool-Use Hook

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous bash commands before they are executed. 

Blocks the following destructive patterns:
- `rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force` or `git push -f`
- `DELETE FROM` (without a `WHERE` clause)

When a command is blocked, Claude receives a clear explanation, and the attempt is logged to `~/.claude/hooks/blocked.log` with the timestamp, command, and project path.

## Installation

You can install this hook in 2 commands:

```bash
mkdir -p ~/.claude/hooks/
curl -o ~/.claude/hooks/pre-tool-use https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/safe-bash/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use
```

*(Note: Claude Code will automatically detect and run the `pre-tool-use` script before any tool execution)*
