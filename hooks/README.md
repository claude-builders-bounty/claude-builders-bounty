# 🔒 Pre-Tool-Use Hook — Claude Code Security

Blocks dangerous bash commands before execution in Claude Code.

## Installation

```bash
# One command install
bash hooks/install.sh
```

Or manually:

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use-hook.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /project/node_modules` | Destructive deletion |
| `DROP TABLE` | `DROP TABLE users;` | Data loss |
| `git push --force` | `git push --force origin main` | History rewrite |
| `TRUNCATE` | `TRUNCATE sessions;` | Mass deletion |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Mass deletion |
| `chmod -R 777` | `chmod -R 777 /var/www` | Security risk |
| `mv * /dev/null` | `mv logs/* /dev/null` | Data destruction |

## Logs

Blocked commands are logged to `~/.claude/hooks/blocked.log`:

```
[2026-07-06T11:30:00] BLOCKED: rm -rf node_modules | Pattern: rm -rf | Project: /home/user/project
```

## Testing

```bash
# Test with a dangerous command
echo '{"command": "rm -rf /tmp/test"}' | python3 hooks/pre-tool-use-hook.py
# Should output: {"action": "block", "message": "..."}

# Test with a safe command
echo '{"command": "npm install"}' | python3 hooks/pre-tool-use-hook.py
# Should output: {"action": "allow"}
```
