# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code safety hook that intercepts and blocks dangerous bash commands before execution.

## Installation

```bash
# 1. Copy hook to Claude Code hooks directory
mkdir -p ~/.claude/hooks
cp block-destructive.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-destructive.py

# 2. Register in Claude Code settings (~/.claude/settings.json)
# Add to "hooks" section:
# "pre_tool_use": ["~/.claude/hooks/block-destructive.py"]
```

## What It Blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` / `rm -fr` | `rm -rf /`, `rm -fr ./data` |
| `DROP TABLE` | `DROP TABLE users` |
| `TRUNCATE` | `TRUNCATE TABLE logs` |
| `DELETE FROM` without WHERE | `DELETE FROM users` |
| `DELETE FROM` with `WHERE 1=1` | `DELETE FROM users WHERE 1=1` |
| `git push --force` / `-f` | `git push -f origin main` |
| `mkfs.*` | `mkfs.ext4 /dev/sda1` |
| `dd` to device | `dd if=img of=/dev/sda` |
| Write to block device | `> /dev/sda` |
| `chmod 777 /` | `chmod -R 777 /` |

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-09-03T12:00:00+00:00] BLOCKED | project=/home/user/myapp | reason=Matches dangerous pattern: rm\s+... | command=rm -rf /tmp/data
```

## Behavior

- **Non-shell tools**: Always allowed (pass-through)
- **Safe shell commands**: Allowed normally
- **Blocked commands**: Returns clear error message explaining why
- **Hook errors**: Fail-open (allows command, logs warning)

## Testing

```bash
# Test blocking
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /"},"project_path":"/test"}' | python3 block-destructive.py

# Test allowing
echo '{"tool_name":"bash","tool_input":{"command":"ls -la"},"project_path":"/test"}' | python3 block-destructive.py
```
