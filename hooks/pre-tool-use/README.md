# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code `PreToolUse` hook that intercepts and blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
cd hooks/pre-tool-use
python3 install.py
```

That's it. The installer copies the hook to `~/.claude/hooks/` and registers it in `~/.claude/settings.json`.

## What Gets Blocked

| Pattern | Reason |
|---------|--------|
| `rm -rf` / `rm -fr` | Recursive force delete |
| `DROP TABLE` / `DROP DATABASE` | Irreversible data loss |
| `TRUNCATE TABLE` | Removes all rows without logging |
| `DELETE FROM` (no WHERE) | Deletes all rows |
| `git push --force` / `-f` | Rewrites remote history |
| `mkfs` | Formats filesystem |
| `dd of=/dev/...` | Overwrites disk |
| `chmod -R 777 /` | Removes all file permissions |

## What's Allowed

- Normal `rm file.txt` (no recursive force)
- `DELETE FROM table WHERE condition` (has WHERE clause)
- `git push origin main` (no force flag)
- `git push --force-with-lease` (safe force push)
- All non-Bash tool calls pass through untouched

## Logging

Every blocked command is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Attempted command
- Project path
- Block reasons

## Testing

```bash
python3 -m unittest test_block_destructive_bash.py -v
```

## How It Works

1. Claude Code calls the `PreToolUse` hook before executing any Bash command
2. The hook receives JSON on stdin with `tool_name` and `tool_input`
3. If `tool_name == "Bash"`, the command is checked against dangerous patterns
4. Exit code `0` = allow, exit code `2` = block (stderr message shown to Claude)
