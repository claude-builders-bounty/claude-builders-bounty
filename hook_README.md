# pre-tool-use Hook: Block Destructive Bash Commands

Blocks dangerous commands before execution in Claude Code.

## Installation

```bash
mkdir -p ~/.claude/hooks && curl -o ~/.claude/hooks/pre-tool-use https://raw.githubusercontent.com/USERNAME/claude-builders-bounty/main/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

**Or just copy the file:**
```bash
cp pre-tool-use ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /` |
| `DROP TABLE` | `DROP TABLE users;` |
| `git push --force` | `git push --force origin main` |
| `TRUNCATE` | `TRUNCATE TABLE orders;` |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` |

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Attempted command
- Project path
