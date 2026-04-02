# Claude Code Pre-Tool-Use Security Guard

A production-quality pre-tool-use hook that intercepts dangerous shell commands
**before** Claude executes them, logs every blocked attempt, and explains exactly
why the command was stopped and what safer alternatives exist.

---

## Quick Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -fsSL https://raw.githubusercontent.com/<your-fork>/pre_tool_use_guard.py \
     -o ~/.claude/hooks/pre_tool_use_guard.py && chmod +x ~/.claude/hooks/pre_tool_use_guard.py
```

> **Or copy manually:**
> Copy `pre_tool_use_guard.py` to `~/.claude/hooks/` and `chmod +x` it.

---

## Register the Hook in Claude Code

Add the following to your `~/.claude/settings.json` (create it if it doesn't exist):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use_guard.py"
          }
        ]
      }
    ]
  }
}
```

---

## What It Blocks

| Pattern | Reason |
|---|---|
| `rm -rf` | Recursive force-delete — permanently removes files, no confirmation |
| `git push --force` / `-f` | Rewrites remote history, destroys teammates' commits |
| `DROP TABLE` | Permanently deletes a database table and all its data |
| `TRUNCATE <table>` | Instantly erases all rows, non-transactional in most DBs |
| `DELETE FROM <table>` *(no WHERE)* | Deletes every row in a table — almost always a mistake |
| `git reset --hard` | Discards all uncommitted changes, moves HEAD back irreversibly |
| `git clean -fd` | Permanently deletes untracked files and directories |
| `DROP DATABASE` | Destroys an entire database and all its data |

---

## Block Log

Every blocked attempt is written to `~/.claude/hooks/blocked.log`:

```
# Claude Code Blocked Commands Log
# Format: ISO timestamp | pattern matched | project path | command

2026-03-31T14:22:05+00:00 | rm -rf (recursive force delete) | /home/alex/myproject | rm -rf ./build
2026-03-31T14:25:12+00:00 | SQL DROP TABLE | /home/alex/myproject | DROP TABLE users;
```

---

## Design Decisions

- **Python 3 stdlib only** — zero dependencies, works out of the box.
- **Allow-by-default** — if the payload can't be parsed or the tool name isn't `Bash`,
  the hook exits `0` (allow) so legitimate work is never silently blocked.
- **Pattern granularity** — each rule has a distinct regex and a unique, actionable
  error message explaining safer alternatives. Claude can use these to self-correct.
- **No performance overhead** — the hook runs in < 5 ms on any modern system.

---

## Testing

```bash
# Should be BLOCKED (exit 1):
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"}}' \
  | python3 ~/.claude/hooks/pre_tool_use_guard.py; echo "Exit: $?"

echo '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}' \
  | python3 ~/.claude/hooks/pre_tool_use_guard.py; echo "Exit: $?"

echo '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM users;"}}' \
  | python3 ~/.claude/hooks/pre_tool_use_guard.py; echo "Exit: $?"

echo '{"tool_name":"Bash","tool_input":{"command":"git reset --hard HEAD~1"}}' \
  | python3 ~/.claude/hooks/pre_tool_use_guard.py; echo "Exit: $?"

echo '{"tool_name":"Bash","tool_input":{"command":"git clean -fd"}}' \
  | python3 ~/.claude/hooks/pre_tool_use_guard.py; echo "Exit: $?"

echo '{"tool_name":"Bash","tool_input":{"command":"DROP DATABASE production;"}}' \
  | python3 ~/.claude/hooks/pre_tool_use_guard.py; echo "Exit: $?"

# Should be ALLOWED (exit 0):
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' \
  | python3 ~/.claude/hooks/pre_tool_use_guard.py; echo "Exit: $?"

echo '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM sessions WHERE expires_at < NOW();"}}' \
  | python3 ~/.claude/hooks/pre_tool_use_guard.py; echo "Exit: $?"

echo '{"tool_name":"Bash","tool_input":{"command":"git stash"}}' \
  | python3 ~/.claude/hooks/pre_tool_use_guard.py; echo "Exit: $?"
```

---

## Requirements

- Python 3.6+ (uses only `json`, `sys`, `os`, `re`, `datetime` — all stdlib)
- Claude Code with hooks support

---

## License

MIT
