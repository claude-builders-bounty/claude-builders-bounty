# 🛡️ Claude Code Safety Hook (Pre-Tool-Use)

A production-ready pre-tool-use hook that intercepts and blocks destructive bash and SQL commands before execution.

## 🚫 Blocked Patterns
- `rm -rf` / `--recursive --force`
- `git push --force` / `-f`
- `DROP TABLE`
- `TRUNCATE TABLE`
- `DELETE FROM` without a `WHERE` clause

## 🚀 2-Command Installation

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use.py ~/.claude/hooks/
```

## 📋 Audit Logging
Every intercepted command is logged to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.
