# Destructive Command Blocker Hook

Pre-tool-use hook for Claude Code that blocks dangerous bash commands.

## Installation (2 commands)

```bash
cp hooks/block-destructive.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-destructive.sh
```

## Features

- Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM`
- Logs all blocked attempts to `~/.claude/hooks/blocked.log`
- Clear error messages explaining why commands are blocked
- Does not interfere with normal bash commands

## How It Works

The hook intercepts bash commands before execution and checks against a list of dangerous patterns.
When a match is found, the command is blocked and logged.
