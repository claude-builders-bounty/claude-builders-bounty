# Pre-Tool-Use Safety Hook for Claude Code

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash
commands before they are executed by Claude Code.

## Installation (2 Commands)

```bash
# 1. Copy the hook
mkdir -p ~/.claude/hooks && cp pre-tool-use ~/.claude/hooks/

# 2. Make it executable
chmod +x ~/.claude/hooks/pre-tool-use
```

Done. Claude Code will now use this hook automatically on every tool call.

## What It Blocks

| Pattern | Why | Safe Alternative |
|---------|-----|-----------------|
| `rm -rf /`, `rm -rf ~`, `rm -rf .` | Destroys system home or entire project | Use explicit paths like `rm -rf node_modules` |
| `DROP TABLE` | Accidental data loss | Use `DROP TABLE IF EXISTS` with migration |
| `git push --force` | Destroys remote history | Use `git push --force-with-lease` |
| `TRUNCATE` | Unrecoverable data deletion | Use `DELETE FROM ... WHERE ...` |
| `DELETE FROM` without `WHERE` | Mass data deletion | Always add a `WHERE` clause |
| `mkfs`, `dd if=`, `format`, `fdisk` | Disk destruction | N/A — manual operation only |
| `chmod 777` | Security risk | Use `755` for directories, `644` for files |
| `chown -R` without explicit path | Unintended ownership changes | Specify exact paths |

## How It Works

Claude Code calls this hook before every tool execution. The hook:
1. Reads the JSON input from stdin (containing the command to execute)
2. Checks for dangerous patterns using regex
3. If blocked: logs to `~/.claude/hooks/blocked.log` and exits with code 1
4. If safe: exits with code 0 and the command proceeds

## Blocked Commands Log

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Attempted command
- Block reason
- Project path

## Testing

```bash
# Test that safe commands pass through
echo '{"command": "ls -la"}' | python3 pre-tool-use
echo '{"command": "rm -rf node_modules"}' | python3 pre-tool-use

# Test that dangerous commands are blocked
echo '{"command": "rm -rf /"}' | python3 pre-tool-use
echo '{"command": "git push --force"}' | python3 pre-tool-use
```

## Requirements

- Python 3.6+
- Claude Code (for hook integration)

## Files

| File | Purpose |
|------|---------|
| `pre-tool-use` | The hook script (install to `~/.claude/hooks/`) |
| `blocked.log` | Audit log of blocked commands (auto-created) |
| `README.md` | This file |
