# pre-tool-use: Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that intercepts dangerous shell commands
before they are executed, logs every blocked attempt, and explains to Claude
why the command was blocked.

---

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre_tool_use
curl -o ~/.claude/hooks/pre_tool_use/block_destructive_commands.py \
  https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre_tool_use/block_destructive_commands.py \
  && chmod +x ~/.claude/hooks/pre_tool_use/block_destructive_commands.py
```

Then add the hook to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "pre_tool_use": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use/block_destructive_commands.py"
          }
        ]
      }
    ]
  }
}
```

---

## What It Blocks

| Pattern | Example | Why |
|---|---|---|
| `rm -rf` | `rm -rf /var/data` | Recursive force delete — unrecoverable |
| `DROP TABLE` | `DROP TABLE users;` | Destroys entire database table |
| `git push --force` | `git push origin main --force` | Rewrites remote history |
| `TRUNCATE` | `TRUNCATE TABLE orders;` | Deletes all rows from a table |
| `DELETE FROM` without `WHERE` | `DELETE FROM logs;` | Deletes every row in a table |

Commands that do **not** match these patterns pass through without interference.

---

## Blocked Attempt Log

Every blocked command is appended to `~/.claude/hooks/blocked.log`:

```
[2026-03-15T14:22:01.123456] BLOCKED: rm -rf (recursive force delete)
  Command: rm -rf ./dist
  Project: /home/user/my-project
────────────────────────────────────────────────────────────
[2026-03-15T14:35:44.987654] BLOCKED: DELETE FROM without a WHERE clause (destructive SQL)
  Command: DELETE FROM sessions;
  Project: /home/user/my-project
────────────────────────────────────────────────────────────
```

View the log at any time:

```bash
cat ~/.claude/hooks/blocked.log
```

---

## How It Works

1. Claude Code calls the hook with a JSON payload on `stdin` describing the
   tool name (`Bash`) and the command string.
2. The hook checks the command against the blocked patterns using regular
   expressions (case-insensitive where appropriate).
3. **If blocked:** the hook writes a `{"action": "block", "message": "..."}` 
   response so Claude receives a clear explanation, and appends a record to
   `blocked.log`.
4. **If safe:** the hook writes `{"action": "allow"}` and exits — zero impact
   on normal workflow.

---

## Requirements

- Python 3.7+  (no third-party dependencies)
- Claude Code with hooks support

---

## License

MIT