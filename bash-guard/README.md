# bash-guard 🛡️

Claude Code `pre-tool-use` hook that blocks destructive bash commands before execution.

## Install

```bash
cp hook.py ~/.claude/hooks/
```

Done. Zero dependencies, stdlib Python only.

## What it blocks

| Pattern | Example | Why blocked |
|---------|---------|-------------|
| `rm -rf` | `rm -rf /` | Irreversible deletion |
| `DROP TABLE` | `DROP TABLE users` | Destroys table + data |
| `git push --force` | `git push origin main --force` | Overwrites remote history |
| `TRUNCATE` | `TRUNCATE logs` | Deletes all rows without logging |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` | Deletes every row |

Safe commands pass through unchanged.

## Test it

```bash
cd bash-guard
# Blocked
echo '{"tool_use":{"name":"bash","input":{"command":"rm -rf /"}}}' | python3 hook.py
echo '{"tool_use":{"name":"bash","input":{"command":"DROP TABLE users"}}}' | python3 hook.py
echo '{"tool_use":{"name":"bash","input":{"command":"DELETE FROM users;"}}}' | python3 hook.py

# Allowed
echo '{"tool_use":{"name":"bash","input":{"command":"ls -la"}}}' | python3 hook.py
echo '{"tool_use":{"name":"bash","input":{"command":"DELETE FROM users WHERE id=1"}}}' | python3 hook.py
```

## Log format

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
2026-05-18T07:56:05Z | rm -rf / | /home/ubuntu/bounty-work/bash-guard | BLOCKED: rm -rf is destructive — use rm -i or specify exact files
```

Format: `timestamp | command | cwd | reason`

## How it works

1. Claude Code calls the hook with JSON on stdin before executing any tool
2. The hook checks if the tool is `bash`
3. It regex-matches the command against destructive patterns
4. If matched: replaces command with `echo 'BLOCKED: reason'` + logs to file
5. If safe: passes through unchanged
6. Outputs JSON on stdout for Claude to process

## Hook output

When blocking, the hook returns:

```json
{
  "tool_use": {
    "name": "bash",
    "input": {
      "command": "echo 'BLOCKED by bash-guard: rm -rf is destructive — use rm -i or specify exact files. Command was: rm -rf /'"
    }
  },
  "message": "⚠️ bash-guard blocked destructive command: rm -rf /\nReason: rm -rf is destructive — use rm -i or specify exact files"
}
```

Claude sees the `message` field and explains why the command was blocked.

## Acceptance Criteria (Bounty #3)

| Criteria | Status |
|----------|--------|
| Claude Code hooks format | ✅ `~/.claude/hooks/hook.py` |
| Block `rm -rf` | ✅ tested |
| Block `DROP TABLE` | ✅ tested |
| Block `git push --force` | ✅ tested |
| Block `TRUNCATE` | ✅ tested |
| Block `DELETE FROM` without WHERE | ✅ tested |
| Log every block to `~/.claude/hooks/blocked.log` | ✅ timestamp + command + cwd + reason |
| Display clear message to Claude | ✅ `message` field in JSON output |
| Does not interfere with safe commands | ✅ `ls`, `DELETE WHERE`, etc pass through |
| Install in ≤2 commands | ✅ `cp hook.py ~/.claude/hooks/` |
