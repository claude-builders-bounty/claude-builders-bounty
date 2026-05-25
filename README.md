# Pre-Tool-Use Hook: Block Dangerous Bash Commands

A [Claude Code pre-tool-use hook](https://docs.anthropic.com/claude-code/hooks) that intercepts and blocks destructive bash commands before execution.

## 🚀 Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -s https://raw.githubusercontent.com/cendd/claude-builders-bounty/main/pre-tool-use.sh -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

That's it! The hook activates on the next Claude Code session.

## 🔒 Blocked Patterns

| Pattern | Example |
|---------|---------|
| Recursive delete | `rm -rf /`, `rm -rf --no-preserve-root` |
| Database destruction | `DROP TABLE users`, `TRUNCATE TABLE orders` |
| Force push | `git push --force origin main` |
| Unsafe delete | `DELETE FROM users` (without WHERE) |

## 📋 Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Project path
- Attempted command

## ⚡ Override

If you're absolutely sure a command is safe, run with:
```bash
BLOCKING_OVERRIDE=1 your-command
```

## ✅ Normal commands are NOT affected

Safe commands like `ls`, `cp`, `mv`, `git add`, `git commit`, `pip install`, `npm run` pass through without any delay or modification.
