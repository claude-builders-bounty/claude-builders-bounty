# block-destructive-commands

A Claude Code **pre-tool-use hook** that intercepts destructive bash commands before they execute, keeping your system and databases safe.

## What it blocks

| Pattern | Example |
|---|---|
| `rm -rf` | `rm -rf /`, `rm -r -f .`, `rm --recursive --force dir` |
| `DROP TABLE` | `psql -c "DROP TABLE users"` |
| `git push --force` | `git push --force origin main`, `git push -f` |
| `TRUNCATE` | `mysql -e "TRUNCATE orders"` |
| `DELETE FROM` (no WHERE) | `sqlite3 db.sqlite "DELETE FROM users"` |

Detection is case-insensitive and handles extra whitespace, flag reordering (`rm -fr`, `rm -r -f`), and long-form flags (`--recursive --force`).

Commands that include a `WHERE` clause with `DELETE FROM` are allowed through.

## Installation

```bash
mkdir -p ~/.claude/hooks && cp block_destructive.sh ~/.claude/hooks/
```

Then add the hook to your `.claude/settings.json` (project or user level):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/block_destructive.sh"
          }
        ]
      }
    ]
  }
}
```

## How it works

1. Claude Code invokes the hook **before** every tool use, piping a JSON payload to stdin containing `tool_name` and `tool_input`.
2. The script checks whether `tool_name` is `"Bash"`. Non-Bash tools are immediately allowed.
3. The command string is normalized (lowercased, whitespace collapsed) and matched against the destructive patterns listed above.
4. If a pattern matches, the script:
   - Logs the attempt to `~/.claude/hooks/blocked.log` (timestamp, command, project path) in JSON-lines format.
   - Returns `{"decision":"block","reason":"..."}` so Claude Code prevents execution.
5. If no pattern matches, it returns `{"decision":"allow"}`.

## Blocked-command log

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as a JSON-lines entry:

```json
{"timestamp":"2026-05-13T10:30:00Z","project":"/home/user/myproject","reason":"Destructive command blocked: rm with recursive and force flags (rm -rf)","command":"rm -rf /tmp/important"}
```

## Requirements

- `jq` (for JSON parsing)
- `bash` 4+
- `grep` with `-E` (extended regex) support
