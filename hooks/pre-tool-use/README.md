# Safe Bash Pre-Tool-Use Hook 🛡️

A security hook for Claude Code that intercepts and blocks dangerous bash commands before execution.

## Features
- Blocks high-risk patterns: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` (without WHERE).
- Logs blocked attempts to `~/.claude/hooks/blocked.log`.
- Provides clear feedback to Claude explaining the block.

## Installation

```bash
# 1. Create the hooks directory
mkdir -p ~/.claude/hooks

# 2. Copy the hook script
cp hooks/pre-tool-use/safe-bash.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/safe-bash.py
```

## How it works
The hook scans the command string for dangerous patterns using regex. If a match is found, it exits with code `1`, which prevents Claude Code from executing the command.
