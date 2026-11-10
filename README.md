# Block Destructive Commands Hook

## Installation

1. Copy the hook script to the hooks directory:
   ```bash
   cp block-destructive-commands ~/.claude/hooks/
   ```

2. Make the hook executable:
   ```bash
   chmod +x ~/.claude/hooks/block-destructive-commands
   ```

## Features

- Blocks destructive commands like `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a WHERE clause.
- Logs blocked attempts to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.
- Displays a clear message explaining the block.
- Does not interfere with normal bash commands.