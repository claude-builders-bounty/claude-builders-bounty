# block-destructive — Claude Code PreToolUse Hook

A safety hook that intercepts and blocks destructive bash commands before Claude Code executes them. Protects against accidental `rm -rf`, `DROP TABLE`, `git push --force`, and other irreversible operations.

## Install (2 commands)

```bash
cp hooks/block-destructive.sh ~/.claude/hooks/block-destructive.sh
```

Then add the hook to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "bash ~/.claude/hooks/block-destructive.sh",
        "description": "Block destructive bash commands"
      }
    ]
  }
}
```

## What it blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` | Recursive force deletion can destroy entire directory trees |
| `DROP TABLE` / `DROP DATABASE` | Permanently destroys database objects |
| `TRUNCATE` | Removes all rows without per-row logging |
| `DELETE FROM ... ;` (no WHERE) | Deletes every row in a table |
| `git push --force` / `-f` | Overwrites remote history |
| `git reset --hard` | Discards all uncommitted changes |
| `git clean -f` | Permanently removes untracked files |
| `chmod 777` | Sets world-readable/writable/executable — a security risk |
| `mkfs.*` | Formats a filesystem |
| `dd ... of=/dev/` | Raw disk write |

## What happens when a command is blocked

1. The command is **not executed**
2. Claude receives a clear message explaining why
3. The attempt is logged to `~/.claude/hooks/blocked.log` with:
   - Timestamp (UTC)
   - Block reason
   - Full command
   - Project path

## Log format

```
2026-05-11T10:30:00Z | BLOCKED | rm -rf: recursive force deletion | command: rm -rf / | project: /home/user/myproject
```

## Safe commands pass through

Normal operations like `rm file.txt`, `git push`, `DELETE FROM users WHERE id = 5;` are **not blocked** — only the dangerous variants without safeguards.

## Testing

```bash
# Simulate a blocked command
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | bash hooks/block-destructive.sh
# Expected: exit code 2, stderr shows BLOCKED message

# Simulate a safe command
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | bash hooks/block-destructive.sh
# Expected: exit code 0, original JSON passed through
```
