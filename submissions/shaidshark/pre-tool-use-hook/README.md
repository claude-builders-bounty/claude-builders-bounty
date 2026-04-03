# Pre-tool-use Hook: Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous shell commands before execution.

## Blocked Patterns

| Pattern | Risk Level | Example |
|---------|-----------|---------|
| `rm -rf` | CRITICAL | `rm -rf /var/data` |
| `git push --force` | HIGH | `git push --force origin main` |
| `DROP TABLE` | CRITICAL | `DROP TABLE users;` |
| `TRUNCATE` | HIGH | `TRUNCATE logs;` |
| `DELETE FROM` without `WHERE` | CRITICAL | `DELETE FROM users;` |

## Installation

```bash
mkdir -p ~/.claude/hooks
cp hook.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

Add to your Claude Code hooks config (`~/.claude/hooks.json`):

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "command": "python3 ~/.claude/hooks/pre-tool-use.py",
        "tools": ["bash", "shell"]
      }
    ]
  }
}
```

## Override

To allow a blocked command once:

```bash
export ALLOW_DESTRUCTIVE=1
```

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, risk level, and the blocked command.

## Testing

```bash
# Should be blocked (exit 1):
echo "rm -rf /tmp/test" | python3 hook.py

# Should be allowed (exit 0):
echo "ls -la" | python3 hook.py

# Override:
echo "rm -rf /tmp/test" | ALLOW_DESTRUCTIVE=1 python3 hook.py
```
