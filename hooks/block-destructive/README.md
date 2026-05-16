# Block Destructive Commands Hook

A Claude Code pre-tool-use hook that intercepts dangerous bash commands before execution.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh
```

Then add to `~/.claude/hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-destructive.sh"
          }
        ]
      }
    ]
  }
}
```

## What it blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /src` | Recursive force-delete, cannot be undone |
| `DROP TABLE/DATABASE` | `DROP TABLE users;` | Permanently deletes database objects |
| `git push --force` | `git push --force origin main` | Overwrites remote history |
| `TRUNCATE` | `TRUNCATE TABLE logs;` | Deletes all rows without row-level logging |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Deletes ALL rows in the table |

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:

```
[2026-05-16 12:00:00] BLOCKED | cmd='rm -rf /' | project='/home/user/project' | reason='rm -rf detected: ...'
```

## How it works

1. Reads tool input (JSON) from stdin
2. Extracts the bash command
3. Checks against dangerous patterns
4. Returns `block` with a reason, or `allow`

## Test it

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | bash block-destructive.sh
# Expected: {"decision": "block", "reason": "rm -rf with root/home/glob detected: ..."}

echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | bash block-destructive.sh
# Expected: {"decision": "allow"}
```
