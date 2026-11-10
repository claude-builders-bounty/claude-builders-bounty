# Block Destructive Commands Hook

## Installation
1. Create the hook file: `touch ~/.claude/hooks/block-destructive-commands`
2. Add the above script content to the file and make it executable: `chmod +x ~/.claude/hooks/block-destructive-commands`

## Features
- Blocks: `rm -rf`, `git push --force`, `DROP TABLE`, `TRUNCATE`, `DELETE FROM` without a WHERE clause
- Logs blocked attempts to `~/.claude/hooks/blocked.log`
- Displays a clear message explaining the block