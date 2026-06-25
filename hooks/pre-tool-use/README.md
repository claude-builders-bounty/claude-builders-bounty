# Pre-Tool-Use Hook: Block Dangerous Commands

## Installation
```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use.py
```

## What it blocks
- `rm -rf`
- `DROP TABLE` / `DROP DATABASE`
- `git push --force`
- `TRUNCATE` / `DELETE FROM` without WHERE
- `chmod 777`
- `dd if=`
- Pipe to shell from curl/wget
- Direct block device writes

## Override
Add `#allow-dangerous` at the end of the command.
