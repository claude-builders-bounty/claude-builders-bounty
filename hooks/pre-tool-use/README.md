# Pre-Tool-Use Hook: Destructive Command Blocker

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before they execute.

## What it blocks

- `rm -rf` without relative path (e.g., `rm -rf /`)
- SQL DDL statements (`DROP TABLE`, `TRUNCATE`, `ALTER ... DROP`)
- `DELETE FROM` without `WHERE` clause
- `git push --force` (not `--force-with-lease`)
- Filesystem operations (`mkfs`, `chmod -R 000 /`)

## What it allows (safe overrides)

- `rm -rf ./node_modules` (relative paths)
- `DROP TABLE IF EXISTS` (migration-safe)
- `DELETE FROM ... WHERE ...` (scoped deletes)
- `git push --force-with-lease` (safer force push)

## Installation

**2 commands:**

```bash
# 1. Download the hook
curl -o ~/.claude/hooks/pre-tool-use/blocker.py https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre-tool-use/blocker.py

# 2. Make it executable
chmod +x ~/.claude/hooks/pre-tool-use/blocker.py
```

That's it! Claude Code will now automatically block destructive commands.

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-06-15T00:00:00] BLOCKED: command='rm -rf /' reason='Matched destructive pattern: rm -rf without relative path' project='/home/user/project'
```

## Configuration

Edit the `DESTRUCTIVE_PATTERNS` and `SAFE_OVERRIDES` lists in `blocker.py` to customize behavior.

## Testing

```bash
# Test the hook directly
echo '{"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}, "cwd": "/test"}' | python3 blocker.py
# Should output: {"decision": "deny", "reason": "..."}

# Test safe command
echo '{"tool_name": "Bash", "tool_input": {"command": "rm -rf ./node_modules"}, "cwd": "/test"}' | python3 blocker.py
# Should output: {"decision": "allow"}
```

## Requirements

- Python 3.6+
- No external dependencies
