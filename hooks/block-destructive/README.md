# Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

Intercepts dangerous bash commands before execution in Claude Code.

## Blocked Patterns

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /usr/local` |
| `DROP TABLE` | `DROP TABLE users;` |
| `git push --force` | `git push origin main --force` |
| `TRUNCATE` | `TRUNCATE TABLE logs;` |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` |
| `curl \| sh` pipe patterns | `curl xxx \| bash` |
| `chmod 777` | `chmod 777 /etc/config` |

## Safe Patterns (Allowed)

- `rm -rf node_modules`
- `rm -rf __pycache__`
- `rm -rf dist/ build/ .next/`

## Setup (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/block-destructive/pre-tool-use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use.py
```

## How It Works

1. Claude Code calls this hook before executing any bash command
2. The hook scans the command against 14 dangerous patterns
3. If matched: blocks execution, logs to `~/.claude/hooks/blocked.log`, displays clear explanation
4. Known safe patterns (node_modules cleanup, cache clearing) are automatically allowed
5. Log format: timestamp, attempted command, project path

## Log Example

```
[2026-05-16T15:30:00] BLOCKED: Deleting files recursively (rm -rf)
  Command: rm -rf /etc/nginx
  Project: /home/user/myproject
```

## Claude Code Configuration

Add to your Claude Code settings to enable this hook:

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "hooks": ["~/.claude/hooks/pre-tool-use.py"]
      }
    ]
  }
}
```
