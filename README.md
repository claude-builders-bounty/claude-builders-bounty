# Block Destructive Commands Hook

## Installation

1. Create the hook file:
   ```bash
   mkdir -p ~/.claude/hooks
   echo '#!/bin/bash\n\n# Check if the command is a destructive operation\nif [[ "$@" =~ (rm\s+-rf|DROP\s+TABLE|git\s+push\s+--force|TRUNCATE|DELETE\s+FROM) ]]; then\n  echo "[BLOCKED] Destructive command detected: $@" >> ~/.claude/hooks/blocked.log\n  echo "Error: This command is blocked to prevent accidental data loss."\n  exit 1\nfi\n\n# If not destructive, allow the command to proceed\nexit 0' > ~/.claude/hooks/block-destructive-commands
   ```

2. Make the hook executable:
   ```bash
   chmod +x ~/.claude/hooks/block-destructive-commands
   ```

## Features
- Blocks destructive commands like `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a WHERE clause.
- Logs blocked attempts to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.
- Displays a clear message explaining the block.
- Does not interfere with normal commands.