# Bash Guard Hook

Blocks destructive bash commands in Claude Code (`rm -rf`, `DROP TABLE`, `git push --force`, etc.).

## Install

```bash
mkdir -p ~/.claude/hooks && cp on_tool_use.py ~/.claude/hooks/pre_tool_use.py && chmod +x ~/.claude/hooks/pre_tool_use.py
```

## How It Works

- Claude Code runs the hook before every tool call
- If a blocked pattern is detected, the command is rejected with a clear message
- All blocked attempts are logged to `~/.claude/hooks/blocked.log`

## Blocked Patterns

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause
