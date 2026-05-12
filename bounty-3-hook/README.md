# Pre-Tool-Use Hook: Destructive Command Blocker

A Claude Code hook that intercepts Bash tool calls and blocks known destructive
commands before they execute. Every blocked attempt is logged with a timestamp,
the attempted command, and the project path.

## Installation (2 commands)

```bash
cp hook.sh ~/.claude/hooks/hook.sh && chmod +x ~/.claude/hooks/hook.sh
cp settings.json ~/.claude/settings.json
```

> If you already have a `~/.claude/settings.json`, merge the `hooks` key from
> `settings.json` into your existing file instead of overwriting it.

## What It Blocks

| Pattern | Example |
|---|---|
| `rm -rf` / `rm -r` on system or home paths | `rm -rf /`, `rm -rf ~/` |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;` |
| `git push --force` / `git push -f` | `git push origin main --force` |
| `TRUNCATE TABLE` | `TRUNCATE TABLE orders;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` |
| `git reset --hard` | `git reset --hard HEAD~3` |
| `git clean -f` (and variants) | `git clean -fd`, `git clean -fdx` |

## What It Allows

- Normal `rm` commands on project files (e.g., `rm -rf ./build`)
- `DELETE FROM` with a `WHERE` clause
- `git push` without `--force`
- `git push --force-with-lease` (intentionally allowed -- it is the safe variant)
- All non-Bash tool calls (Read, Write, Edit, etc.)

## Log Location

Blocked attempts are appended to:

```
~/.claude/hooks/blocked.log
```

Each log line contains:

```
[2026-01-15T12:34:56Z] BLOCKED | reason: ... | command: ... | project: /path/to/project
```

## How It Works

1. Claude Code invokes the hook as a **PreToolUse** handler, passing a JSON
   payload on stdin with `tool_name` and `tool_input`.
2. The script checks if `tool_name` is `"Bash"`. Non-Bash tools pass through.
3. The command is extracted from `tool_input.command` and matched against
   destructive patterns using `grep -E` (extended regex).
4. If a match is found the script logs the attempt, prints an explanation to
   stderr (which Claude sees), and exits with code 1 to block execution.
5. If no match is found, the script exits 0 and Claude proceeds normally.

## Requirements

- `bash` (>= 4.0)
- `jq` (for JSON parsing)
- Claude Code with hooks support
