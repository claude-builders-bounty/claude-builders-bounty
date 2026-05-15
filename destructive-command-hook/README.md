
# Destructive Command Guard Hook

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp destructive-command-hook/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
```

## What It Blocks

- `rm -rf /` — recursive root deletion
- `DROP TABLE` / `DROP DATABASE` — SQL table/database destruction
- `TRUNCATE TABLE` — SQL table truncation
- `DELETE FROM table` without `WHERE` — full table deletion
- `git push --force` / `git push --force-with-lease` — force push
- `git reset --hard` — hard reset
- `mkfs`, `fdisk`, `dd if=` — low-level disk operations
- `chmod 777 /`, `chown -R root:root /` — permission escalation on root
- `docker rm -f`, `docker rmi -f`, `docker system prune -f` — force Docker cleanup
- `Remove-Item -Recurse -Force` — PowerShell recursive delete
- `format C:` — Windows format command
- Fork bomb patterns

## How It Works

1. Claude Code calls the hook before executing a bash command
2. The hook reads the command from stdin JSON
3. It checks against 18+ destructive patterns
4. If a match is found: **blocks the command**, logs to `~/.claude/hooks/blocked.log`
5. If safe: allows execution

## Blocked Log Format

```json
{"timestamp": "2026-05-15T17:50:00+00:00", "command": "rm -rf /tmp/bad", "reason": "rm -rf / detected", "project": "/home/user/project"}
```

## Manual Override

If you genuinely need to run a blocked command:
1. Review the command carefully
2. Run it manually in a terminal outside Claude Code
3. Or temporarily disable the hook: `mv ~/.claude/hooks/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py.disabled`

## Testing

```bash
# Test: should block
echo '{"command": "rm -rf /etc/config"}' | python3 pre-tool-use.py
echo '{"command": "DROP TABLE users"}' | python3 pre-tool-use.py
echo '{"command": "git push --force origin main"}' | python3 pre-tool-use.py

# Test: should allow
echo '{"command": "ls -la"}' | python3 pre-tool-use.py
echo '{"command": "git push origin main"}' | python3 pre-tool-use.py
echo '{"command": "npm install"}' | python3 pre-tool-use.py
```

## File Structure

```
destructive-command-hook/
├── README.md
└── pre-tool-use.py
```

## Requirements

- Python 3.8+
- Claude Code (supports hooks)
- No external dependencies
