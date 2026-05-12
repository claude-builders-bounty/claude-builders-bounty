# Destructive Bash Command Guard (Claude Code PreToolUse Hook)

This hook blocks high-risk Bash commands before execution and records each blocked attempt.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp destructive-hook/pre_tool_use_guard.py ~/.claude/hooks/pre_tool_use_guard.py
chmod +x ~/.claude/hooks/pre_tool_use_guard.py
```

## Add to `~/.claude/settings.json`

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

## What it blocks

- `rm -rf` / `rm -fr` (including combined short flags and long options)
- `DROP TABLE`
- `TRUNCATE`
- `git push --force` / `git push -f`
- `DELETE FROM` statements that do not include a `WHERE` clause

## Logs

Blocked attempts are appended to:

```text
~/.claude/hooks/blocked.log
```

Each line includes timestamp, project path, reason, and attempted command.
You can override the log target for CI/tests with `CLAUDE_HOOKS_BLOCKED_LOG=/path/to/blocked.log`.

## Quick check

```bash
printf '%s\n' '{"tool_name":"Bash","cwd":"/tmp/demo","tool_input":{"command":"rm -rf /tmp/test"}}' | python3 destructive-hook/pre_tool_use_guard.py
```

Expected behavior: the hook exits with code `2`, prints a clear block reason, and appends a line to `~/.claude/hooks/blocked.log`.
