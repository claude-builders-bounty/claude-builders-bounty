# Block Dangerous Commands - Claude Code Hook

A Claude Code pre-tool-use hook that blocks destructive bash commands before they are executed.

## Features

- Blocks dangerous file system operations (rm -rf, etc.)
- Blocks destructive database operations (DROP TABLE, TRUNCATE, DELETE without WHERE)
- Blocks dangerous git operations (force push, hard reset, etc.)
- Blocks system destruction commands (mkfs, dd, format)
- Logs all blocked attempts with timestamp and context
- Clear error messages explaining why commands were blocked

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp block-dangerous-commands.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-dangerous-commands.py
```

Or for the bash version:

```bash
mkdir -p ~/.claude/hooks
cp block-dangerous-commands.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-dangerous-commands.sh
```

## Blocked Patterns

### File System
- `rm -rf` / `rm -fr` - Recursive force delete
- `rmdir /` - Deleting root directory

### Database
- `DROP TABLE` - Without safety check
- `TRUNCATE TABLE` - Without safety check
- `DELETE FROM` - Without WHERE clause

### Git
- `git push --force` - Force push to remote
- `git push --delete` - Delete remote branch
- `git reset --hard` - Hard reset (loses changes)
- `git clean -f` - Force clean untracked files
- `git checkout --force` - Force checkout (loses changes)

### System
- `mkfs` - Format filesystem
- `dd if=` - Disk write operation
- `format` - Format disk drive
- `chmod` on system directories
- `chown` on system directories

## Log File

All blocked commands are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Attempted command
- Pattern that triggered the block
- Project path

## Customization

To add or modify blocked patterns, edit the `BLOCKED_PATTERNS` list in the Python version or the `is_blocked()` function in the bash version.

## Testing

Test the hook with:

```bash
echo '{"command": "rm -rf /", "project_path": "/tmp/test"}' | python3 block-dangerous-commands.py
```

## License

MIT
