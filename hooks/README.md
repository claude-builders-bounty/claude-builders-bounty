# Destructive Command Blocker Hook

Pre-tool-use hook that intercepts dangerous bash commands before they're executed in Claude Code.

## What It Blocks

- `rm -rf` and variants (recursive force delete)
- `DROP TABLE` / `DROP DATABASE` (SQL destruction)
- `TRUNCATE TABLE` (removes all data)
- `DELETE FROM` without WHERE clause (removes all rows)
- `git push --force` / `git push -f` (overwrites remote history)
- `mkfs` (filesystem format)
- `dd` to devices (disk overwrite)

## Installation

```bash
# Clone or copy the hook to your Claude hooks directory
mkdir -p ~/.claude/hooks
cp block-destructive-commands.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-destructive-commands.py
```

## How It Works

1. Claude Code calls the hook before executing bash commands
2. Hook checks command against dangerous patterns
3. If blocked:
   - Logs attempt to `~/.claude/hooks/blocked.log`
   - Returns error message to Claude
   - Command is NOT executed
4. If safe: Command executes normally

## Log File

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-06-28T04:35:12.345678] BLOCKED: rm -rf: Recursive force delete
  Command: rm -rf /tmp/test
  Project: /home/user/my-project
--------------------------------------------------------------------------------
```

## Configuration

Edit the `DANGEROUS_PATTERNS` list in `block-destructive-commands.py` to add/remove patterns.

## Testing

```bash
# Test the hook directly
echo '{"tool_name": "bash", "tool_input": {"command": "rm -rf /tmp/test"}}' | \
  python3 ~/.claude/hooks/block-destructive-commands.py
```

Expected output: JSON with `hookFailed: true` and error message.

## License

MIT
