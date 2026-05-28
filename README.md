# Claude Code Safety Hook — Destructive Bash Command Blocker

A pre-tool-use hook for **Claude Code** that intercepts dangerous bash commands
*before* they execute, preventing accidental data loss.

## What it blocks

| Pattern | Example | Risk |
|---|---|---|
| `rm -rf` | `rm -rf /important/dir` | Irreversible recursive deletion |
| `DROP TABLE` | `DROP TABLE users;` | Destroys an entire database table |
| `git push --force` | `git push --force origin main` | Overwrites remote history |
| `TRUNCATE` | `TRUNCATE TABLE logs;` | Deletes all rows, no rollback |
| `DELETE FROM` (no `WHERE`) | `DELETE FROM accounts;` | Wipes every row in the table |

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with a UTC
timestamp, the attempted command, and the project path.

Normal, safe commands pass through untouched — zero overhead.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py
```

Then register the hook in Claude Code by adding this to your
`~/.claude/settings.json` (or your project's `.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "python3 ~/.claude/hooks/pre-tool-use.py"
      }
    ]
  }
}
```

Restart Claude Code and you're protected.

## Testing

Feed the hook a dangerous command manually to verify it works:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"}}' | python3 hooks/pre-tool-use.py
# Expected output: {"decision": "block", "reason": "..."}

echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 hooks/pre-tool-use.py
# Expected output: {"decision": "allow"}
```

## File layout

```
/tmp/bounty-3/
├── hooks/
│   └── pre-tool-use.py   ← the hook script
└── README.md             ← this file
```

## Log format

```
2026-05-28T16:15:00Z | project=/home/jarvis/my-project | command="rm -rf node_modules" | reason=rm -rf (recursive force remove) — can irreversibly delete entire directory trees
```
