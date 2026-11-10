# Block Destructive Commands Hook

## Installation

1. Copy the hook script to the Claude Code hooks directory:
   ```bash
   cp block-destructive-commands ~/.claude/hooks/
   ```

2. Ensure the hook is executable:
   ```bash
   chmod +x ~/.claude/hooks/block-destructive-commands
   ```

## Features

- Blocks commands containing `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, or `DELETE FROM` without a WHERE clause
- Logs blocked attempts to `~/.claude/hooks/blocked.log`
- Displays a clear message explaining the block
- Does not interfere with normal commands