# Destructive Command Blocker — Claude Code Pre-Tool-Use Hook

A security hook for Claude Code that intercepts dangerous bash and SQL commands before execution, preventing accidental data loss or destructive git operations.

## Features
- **Blocks Dangerous Shell Commands**: `rm -rf`, `rm -f`, `mkfs`, `dd` to raw disk devices.
- **Blocks Destructive Database Operations**: `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, and unconditional `DELETE FROM` without a `WHERE` clause.
- **Blocks Destructive Git Operations**: `git push --force`, `git push -f`.
- **Structured Audit Logging**: Logs every intercepted attempt to `~/.claude/hooks/blocked.log` with timestamp, command, reason, and working directory.

---

## 2-Command Installation

```bash
# 1. Create hooks directory and copy hook
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use/block_destructive.py ~/.claude/hooks/pre-tool-use.py

# 2. Make executable
chmod +x ~/.claude/hooks/pre-tool-use.py
```

---

## Testing

Run the included unit test suite:
```bash
python3 hooks/pre-tool-use/test_hook.py
```
