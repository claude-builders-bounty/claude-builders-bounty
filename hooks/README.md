# Block Destructive Bash Commands Hook

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before they are executed.

## What It Blocks

| Pattern | Risk Level | Description |
|---------|-----------|-------------|
| `rm -rf` / `rm -fr` | 🔴 Critical | Recursive force delete |
| `DROP TABLE` | 🔴 Critical | Deletes entire database table |
| `TRUNCATE` | 🔴 Critical | Deletes all rows from table |
| `DELETE FROM` (no WHERE) | 🔴 Critical | Deletes all rows |
| `git push --force` | 🟠 High | Force push overwrites remote history |
| `mkfs` | 🔴 Critical | Formats filesystem |
| `dd of=/dev/` | 🔴 Critical | Writes directly to device |
| `chmod 777` | 🟡 Medium | Grants full permissions (security risk) |
| `chown -R` | 🟡 Medium | Recursive ownership change |
| `shutdown`/`reboot` | 🟠 High | System interruption |

## Installation (2 commands)

```bash
# 1. Copy the hook to your hooks directory
cp hooks/block-destructive-commands.py ~/.claude/hooks/

# 2. Make it executable
chmod +x ~/.claude/hooks/block-destructive-commands.py
```

## How It Works

1. Claude Code sends bash commands to the hook before execution
2. The hook checks commands against dangerous patterns
3. If a dangerous command is detected:
   - Command is **blocked** (exit code 2)
   - Attempt is **logged** to `~/.claude/hooks/blocked.log`
   - Clear **error message** is shown to Claude explaining why
4. Safe commands pass through normally

## Log Format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-28T10:30:45.123456] BLOCKED
  Command: rm -rf /tmp/test
  Project: /home/user/project
  Reason: rm -rf: Recursive force delete
============================================================
```

## Testing

```bash
# Test the hook directly
echo '{"tool":"bash","tool_input":{"command":"rm -rf /tmp/test"},"cwd":"/tmp"}' | python3 ~/.claude/hooks/block-destructive-commands.py

# Check the log
cat ~/.claude/hooks/blocked.log
```

## Customization

Edit `DANGEROUS_PATTERNS` in the script to add/remove patterns:

```python
DANGEROUS_PATTERNS = [
    (r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\s', "rm -rf: Recursive force delete"),
    # Add more patterns here...
]
```

## Safety Features

- **Whitelist safe patterns**: Commands like `history`, `grep`, `man`, `--help` are never blocked
- **Graceful errors**: If the hook fails, commands are allowed (don't break Claude Code)
- **Detailed logging**: Every blocked attempt is logged with timestamp, command, and project path
- **Clear messages**: Claude receives explanation of why command was blocked

## Requirements

- Python 3.10+ (uses `str | None` type hint)
- Claude Code with hooks support

## License

MIT
