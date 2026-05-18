# Claude Code Pre-Tool-Use Security Hook

Blocks destructive bash commands before they execute. Protects against accidental data loss from `rm -rf`, unconditioned `DELETE FROM`, `DROP TABLE`, `TRUNCATE`, and `git push --force`.

## Installation (2 commands)

```bash
# 1. Link the hook into your Claude hooks directory
ln -s /path/to/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py

# 2. Create the blocked log file
touch ~/.claude/hooks/blocked.log
```

Replace `/path/to/pre-tool-use.py` with the actual path to wherever you place this script.

## What it blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursively deletes directory trees |
| `git push --force` | Rewrites remote history |
| `DROP TABLE` (no IF EXISTS) | Removes table structure and all data |
| `DELETE FROM` (no WHERE) | Deletes all rows from a table |
| `TRUNCATE` | Removes all rows from a table |

## Blocked log

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with:
- Timestamp (UTC)
- Project path
- Reason
- Full command (truncated at 200 chars)

## How it works

Claude Code invokes the hook with a JSON payload on stdin. The hook inspects the `tool_name` (only acts on `Bash`) and the `command` string, then returns:
- `{"allow": true}` — command proceeds
- `{"allow": false, "error": "..."}` — command is blocked with a message

## Disabling temporarily

If you need to run a blocked command, you can temporarily rename the hook file:
```bash
mv ~/.claude/hooks/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py.disabled
# run your command
mv ~/.claude/hooks/pre-tool-use.py.disabled ~/.claude/hooks/pre-tool-use.py
```
