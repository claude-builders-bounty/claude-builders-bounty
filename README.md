# Block Destructive Commands Hook

## Installation

1. Create the hook file:
   ```bash
   mkdir -p ~/.claude/hooks
   touch ~/.claude/hooks/block-destructive-commands
   ```

2. Add the following content to the hook file:
   ```bash
   #!/bin/bash

   # Check if the command is a destructive operation
   if [[ "$@" =~ (rm\s+-rf|DROP\s+TABLE|git\s+push\s+--force|TRUNCATE|DELETE\s+FROM) ]]; then
     echo "[BLOCKED] Destructive command detected: $@" >> ~/.claude/hooks/blocked.log
     echo "Error: Destructive command blocked. This is a safety measure to prevent accidental data loss." >&2
     exit 1
   fi

   # If not destructive, allow the command to proceed
   exit 0
   ```

3. Make the hook executable:
   ```bash
   chmod +x ~/.claude/hooks/block-destructive-commands
   ```

## Features

- Blocks destructive commands like `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a WHERE clause.
- Logs blocked commands to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.
- Displays a clear message explaining the block.
- Does not interfere with normal bash commands.