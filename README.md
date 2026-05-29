# Claude Code Hook: Block Destructive Bash Commands

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous commands (e.g. `rm -rf`, `DROP TABLE`) from being executed. Logs blocked commands to `~/.claude/hooks/blocked.log`.

## Installation

Run these two commands to install the hook into your Claude Code environment:

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre-tool-use https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use
```

*(Note: If you are pulling from a fork or a specific branch, adjust the raw URL accordingly.)*

## Features

Blocks the following patterns:
- `rm -rf` / `rm -fr`
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE`
- `DELETE FROM` (without a `WHERE` clause)

When a command is blocked, Claude Code will receive a clear message explaining why the command was denied, and the attempt will be logged with a timestamp and the current project path.
