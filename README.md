# Destructive Command Blocker — Claude Code Hook

A `PreToolUse` hook that intercepts dangerous bash commands before Claude Code executes them.

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` / `rm --recursive --force` | Recursive deletion can cause irreversible data loss |
| `DROP TABLE` / `DROP DATABASE` | Destroys schema and data permanently |
| `git push --force` / `-f` / `--force-with-lease` | Rewrites remote history |
| `TRUNCATE [TABLE]` | Removes all rows instantly, no rollback |
| `DELETE FROM <table>` without `WHERE` | Deletes all rows from the table |

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp, command, reason, and working directory.

## Install

```bash
cp hooks/pre-tool-use.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use.py
```

```bash
cp hooks/hooks.json ~/.claude/hooks/hooks.json
```

Restart Claude Code to apply.

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use.py ~/.claude/hooks/hooks.json ~/.claude/hooks/blocked.log
```

## Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"},"cwd":"/tmp"}' \
  | python3 hooks/pre-tool-use.py
# Expected: JSON output with "deny" decision

echo '{"tool_name":"Bash","tool_input":{"command":"npm test"},"cwd":"/tmp"}' \
  | python3 hooks/pre-tool-use.py
# Expected: no output (exit 0, command allowed)

echo '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"},"cwd":"/tmp"}' \
  | python3 hooks/pre-tool-use.py
# Expected: JSON output with "deny" decision

echo '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM users WHERE id = 1"},"cwd":"/tmp"}' \
  | python3 hooks/pre-tool-use.py
# Expected: no output (exit 0, WHERE clause present — allowed)
```
