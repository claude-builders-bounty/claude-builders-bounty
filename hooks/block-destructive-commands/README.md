# Block Destructive Commands Hook

This hook intercepts and blocks dangerous commands (like `rm -rf`, `DROP TABLE`, etc.) before Claude Code executes them.

## Installation

Run these two commands to install the hook:
```bash
mkdir -p ~/.claude/hooks/
cp pre-tool-use.sh ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh
```

## Features
- Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` (without WHERE)
- Logs to `~/.claude/hooks/blocked.log`
