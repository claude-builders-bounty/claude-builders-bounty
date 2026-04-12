# Claude Code Pre-Tool-Use Hook — Security Guard

A `pre-tool-use` hook that intercepts dangerous bash/SQL commands before they execute, protecting your projects from accidental data loss.

## What It Does

- Intercepts Claude Code tool invocations before execution
- Blocks dangerous patterns: `rm -rf`, `DROP TABLE`, `TRUNCATE`, `git push --force`, `DELETE` without WHERE, fork bombs, and more
- Logs every blocked attempt with timestamp, command, pattern matched, and project path
- Displays a clear explanation to Claude explaining why the command was blocked
- Allows all safe commands through without interference

## Installation (2 commands)

```bash
# 1. Copy the hook to your Claude hooks directory
cp pre-tool-use.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use

# 2. (Optional) If using bash version instead:
cp pre-tool-use-hook.sh ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use-hook.sh
```

Claude Code will automatically detect and run hooks from `~/.claude/hooks/`.

## What Gets Blocked

| Pattern | Severity | Why |
|---------|----------|-----|
| `rm -rf /` or `rm -rf /tmp` | CRITICAL | Root deletion |
| `DROP TABLE` / `DROP DATABASE` | CRITICAL | Irreversible schema destruction |
| `rm -rf .git` | HIGH | Destroys version control |
| `TRUNCATE TABLE` | HIGH | Irreversible data deletion |
| `git push --force` | HIGH | Can overwrite shared history |
| `DELETE FROM table;` (no WHERE) | HIGH | Deletes all rows |
| `mkfs`, `dd if=` | CRITICAL | Direct disk operations |
| Fork bomb | CRITICAL | Resource exhaustion |
| `chmod -R 777 /` | HIGH | Security vulnerability |

## What Gets Allowed

All normal development commands pass through freely:
- `rm file.txt` (single file deletion)
- `rm -rf node_modules/` (normal cleanup)
- `git push`, `git commit`, `git merge`
- `DELETE FROM users WHERE id = 123` (safe with WHERE)
- `UPDATE`, `INSERT`, `SELECT`

## Blocked Log

Every blocked attempt is logged to:
```
~/.claude/hooks/blocked.log
```

Format:
```
[2026-04-12 08:15:32] BLOCKED: 'rm -rf / --no-preserve-root' | Pattern: 'Recursive root deletion' (CRITICAL) | Path: /home/user/project
```

## Exit Codes

- `0` = Command allowed
- `1` = Command blocked

## Testing

```bash
# Test the hook directly
echo '{"command": "rm -rf /", "project_path": "/test"}' | python3 pre-tool-use.py
# Should output blocked message and exit 1

echo '{"command": "ls -la", "project_path": "/test"}' | python3 pre-tool-use.py
# Should output continue and exit 0
```

## Auto-Approve Safe Deletes

If Claude needs to delete files legitimately, it can:
1. Ask the user for confirmation first
2. Break the operation into specific file deletions
3. Use `trash` instead of `rm` (recoverable)

## Requirements

- Python 3.7+ (for Python version)
- OR Bash 4+ (for bash version)
- Claude Code with hooks support

## Files

- `pre-tool-use.py` — Python implementation (recommended)
- `pre-tool-use-hook.sh` — Bash implementation (alternative)
- `README.md` — This file
