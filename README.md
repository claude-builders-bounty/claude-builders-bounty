# Block Destructive Commands Hook

## Installation

1. Create the hook directory if it doesn't exist:
   mkdir -p ~/.claude/hooks

2. Save this hook script to ~/.claude/hooks/block-destructive-commands and make it executable:
   chmod +x ~/.claude/hooks/block-destructive-commands

## Features

- Blocks destructive commands like `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a WHERE clause.
- Logs blocked attempts to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.
- Displays a clear message explaining the block.
- Does not interfere with normal bash commands.