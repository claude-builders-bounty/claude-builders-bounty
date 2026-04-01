# Claude Code Safety Hook

Pre-tool-use hook that intercepts and blocks destructive bash commands before execution.

## Setup (3 steps)

1. `mkdir -p ~/.claude/hooks/`
2. `cp safety-hook.py ~/.claude/hooks/pre-tool-use.py`
3. Restart Claude Code

## What it blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /`, `rm -rf /home/user` |
| `DROP TABLE/DATABASE` | `DROP TABLE users;` |
| `git push --force` | `git push -f origin main` |
| `TRUNCATE TABLE` | `TRUNCATE users;` |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` |
| `mkfs` | `mkfs.ext4 /dev/sda1` |
| `dd` to device | `dd if=/dev/zero of=/dev/sda` |
| `chmod 777 /` | `chmod -R 777 /` |
| Fork bombs | `:(){ :|:& };:` |
| `sudo rm` | `sudo rm -rf /` |
| `shutdown/reboot` | `shutdown -h now` |

## What it allows

- `rm temp.txt` (single file, no -rf)
- `rm -f temp.txt` (force but not recursive)
- `git push origin main` (no --force)
- `DELETE FROM users WHERE id = 5;` (has WHERE clause)
- All non-bash tools (file reads, searches, etc.)

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (ISO 8601)
- Full command (truncated to 500 chars)
- Reason for blocking

## Testing

```bash
python3 test_safety_hook.py
```

33 tests covering blocked commands, allowed commands, and non-bash tools.
