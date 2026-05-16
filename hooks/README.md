# Block Destructive Commands — Claude Code Pre-Tool-Use Hook

A safety hook that blocks dangerous bash commands **before** Claude Code executes them. Prevents irreversible data loss from:

| Blocked Pattern | Examples |
|---|---|
| `rm -rf` | `rm -rf /`, `rm -r -f node_modules`, `/bin/rm -rf *` |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;`, `DROP DATABASE prod;` |
| `git push --force` | `git push --force origin main`, `git push -f` |
| `TRUNCATE TABLE` | `TRUNCATE TABLE orders;`, `TRUNCATE users;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` (no WHERE clause) |

**Safe commands pass through untouched** — only the above dangerous patterns are intercepted.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/block-destructive.sh ~/.claude/hooks/block-destructive.sh && chmod +x ~/.claude/hooks/block-destructive.sh
```

That's it. Claude Code automatically discovers and runs hooks from `~/.claude/hooks/`. The hook activates on the next Claude Code session.

## How It Works

1. **Claude Code** sends tool invocation details as JSON on stdin before executing any tool
2. The hook inspects `tool_name` — only acts on Bash/Shell tool calls (everything else passes through)
3. It checks the command against the blocked patterns using regex
4. If blocked: logs to `~/.claude/hooks/blocked.log`, displays a clear message via stderr, and exits non-zero
5. If safe: exits zero and the tool runs normally

## Log Format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-16T07:56:00Z] BLOCKED: rm -rf (recursive force delete)
  Command : rm -rf /tmp/important-data
  Project : /home/user/my-project
---
```

## Manual Override

If you're absolutely sure a blocked command is safe:

- **Option A:** Run it manually in your own terminal (not through Claude Code)
- **Option B:** Temporarily move the hook file out of `~/.claude/hooks/`, run the command, then move it back

## Testing

```bash
# Simulate what Claude Code sends to the hook
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"},"cwd":"/tmp"}' | bash hooks/block-destructive.sh
echo "Exit code: $?"   # Should be 1 (blocked)

echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp"}' | bash hooks/block-destructive.sh
echo "Exit code: $?"   # Should be 0 (allowed)

echo '{"tool_name":"Bash","tool_input":{"command":"rm file.txt"},"cwd":"/tmp"}' | bash hooks/block-destructive.sh
echo "Exit code: $?"   # Should be 0 (safe rm, no -rf)
```
