# Destructive Command Blocker Hook

This Claude Code `PreToolUse` hook blocks common destructive Bash commands before they run.

## What It Blocks

- `rm -rf` style recursive forced deletion
- `git push --force` and `git push --force-with-lease`
- `DROP TABLE`
- `TRUNCATE TABLE`
- `DELETE FROM` without a `WHERE` clause

## Install

1. Copy `hooks/pre_tool_use_block_destructive.py` into your project.
2. Make it executable with `chmod +x hooks/pre_tool_use_block_destructive.py`.
3. Add it to Claude Code hook settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 hooks/pre_tool_use_block_destructive.py"
          }
        ]
      }
    ]
  }
}
```

Blocked commands are logged to `~/.claude/hooks/blocked-destructive-commands.log`.

## Manual Test

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf ./dist"}}' \
  | python3 hooks/pre_tool_use_block_destructive.py
```

The hook exits with status `2` and prints a clear blocking reason to stderr.
