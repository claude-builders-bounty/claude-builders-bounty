# Bash Guard -- Claude Code Pre-Tool-Use Hook

Blocks destructive bash commands before Claude Code executes them.

## Install (2 commands)

```bash
# 1. Copy the hook into your Claude Code hooks directory
cp bash_guard.py ~/.claude/hooks/

# 2. Done. Claude Code will automatically load it on next session start.
```

## What it blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /home/user/project` |
| `DROP TABLE` | `DROP TABLE users;` |
| `TRUNCATE TABLE` | `TRUNCATE TABLE logs;` |
| `git push --force` | `git push origin main --force` |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` |
| `shred` | `shred -u sensitive.txt` |
| `mkfs` | `mkfs.ext4 /dev/sda1` |
| `dd` to disk | `dd if=image.iso of=/dev/sda` |
| Fork bomb | `:(){ :|:& };:` |

## False positives

`rm -rf` in test/temp/build directories is allowed:
```bash
rm -rf node_modules/          # allowed
rm -rf build/                  # allowed
rm -rf /home/user/documents/   # blocked
```

## Logs

Blocked commands are logged to `~/.claude/hooks/blocked.log`:
```
[2026-05-13T18:30:00+00:00] BLOCKED: Matched pattern: rm\s+-rf...
  Command: rm -rf /home/user/documents
  Project: /home/user/project
```

## Customization

Edit `~/.claude/hooks/bash_guard.py` and adjust `BLOCK_PATTERNS` or `SAFE_PATTERNS`.
