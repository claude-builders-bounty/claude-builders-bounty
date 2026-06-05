# Destructive Command Hook for Claude Code

Blocks dangerous bash commands before execution. Works as a `pre-tool-use` hook.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp block-destructive.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-destructive.py
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "command": "python3 ~/.claude/hooks/block-destructive.py"
      }
    ]
  }
}
```

## Blocked Patterns

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /important/dir` |
| `git push --force` | `git push --force origin main` |
| `DROP TABLE` | `DROP TABLE users;` |
| `DROP DATABASE` | `DROP DATABASE production;` |
| `TRUNCATE` | `TRUNCATE orders;` |
| `DELETE FROM` without WHERE | `DELETE FROM users;` |
| `chmod 777` | `chmod 777 /etc/passwd` |
| Fork bomb | `:(){ :|:& };:` |

## Log Format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-06-05T14:30:00Z] BLOCKED 'rm -rf' | cwd=/home/user/project | cmd=rm -rf node_modules
```
