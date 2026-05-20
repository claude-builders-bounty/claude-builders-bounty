# Claude Code Pre-Tool-Use Hook: Destructive Command Blocker

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
# 1. Copy the hook to your Claude hooks directory
cp pre-tool-use.py ~/.claude/hooks/pre-tool-use

# 2. Make it executable
chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf /`, `rm -rf /home` | Attempting to delete root/home filesystem |
| `DROP TABLE` | SQL DROP TABLE command detected |
| `TRUNCATE` | SQL TRUNCATE command detected |
| `git push --force`, `git push -f` | Force push to remote repository |
| `DELETE FROM` without WHERE | SQL DELETE without WHERE clause |

## How It Works

Claude Code invokes the hook before each tool use. The hook:

1. **Reads** the tool input JSON from stdin
2. **Extracts** the bash command (handles various input formats)
3. **Checks** against destructive command patterns
4. **If blocked**: Logs to `~/.claude/hooks/blocked.log` and exits with error
5. **If safe**: Returns the original input unchanged

## Log Format

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-20 22:28:49] BLOCKED: Attempting to delete entire root filesystem | Command: rm -rf / | Path: /Users/ernest
[2026-05-20 22:28:56] BLOCKED: Force push to remote repository | Command: git push --force origin main | Path: /Users/ernest
```

## Error Output

When a command is blocked, the hook prints a clear message:

```
🔒 HOOK: Command Blocked
============================================================
Reason: Attempting to delete entire root filesystem
Command: rm -rf /
Project: /Users/ernest
Log: ~/.claude/hooks/blocked.log
============================================================
To proceed, run this command directly in your terminal.
```

## Testing Results

✅ `rm -rf /` → Blocked (root filesystem)
✅ `rm -rf /home` → Blocked (home directory)
✅ `DROP TABLE users` → Blocked (SQL)
✅ `git push --force` → Blocked (force push)
✅ `TRUNCATE mytable` → Blocked (SQL)
✅ `DELETE FROM users` → Blocked (no WHERE)
✅ `DELETE FROM users WHERE id=1` → Allowed (has WHERE)
✅ `ls -la` → Allowed (safe)
✅ `git log` → Allowed (safe)

## Acceptance Criteria Met

✅ Hook follows Claude Code hooks format (`~/.claude/hooks/`)
✅ Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
✅ Logs every blocked attempt to `~/.claude/hooks/blocked.log` with: timestamp, attempted command, project path
✅ Displays a clear message explaining why the command was blocked
✅ Does not interfere with normal bash commands
✅ README with installation in 2 commands or fewer

## Files

- `pre-tool-use.py` - Main hook script (Python 3.8+)
- `pre-tool-use` - Bash fallback version (optional)
- `README.md` - This file