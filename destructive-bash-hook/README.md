# Destructive Bash Command Guard

Claude Code `PreToolUse` hook that blocks common destructive Bash and SQL commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks
cp destructive-bash-hook/pre_tool_use_guard.py ~/.claude/hooks/pre_tool_use_guard.py && chmod +x ~/.claude/hooks/pre_tool_use_guard.py
```

Add the hook to your Claude Code hooks configuration for Bash `PreToolUse` events:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/pre_tool_use_guard.py"
          }
        ]
      }
    ]
  }
}
```

## What It Blocks

- `rm -rf`, including combined flag variants such as `rm -fr`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Allowed commands exit with status `0` and do not print output. Blocked commands are written to stderr with a clear explanation for Claude, logged to `~/.claude/hooks/blocked.log`, and exit with status `2` so Claude Code stops the tool call.

## Log Format

Each blocked attempt is appended as one JSON line:

```json
{"timestamp":"2026-03-29T12:00:00Z","command":"rm -rf ./dist","project_path":"/path/to/project","reason":"blocks rm -rf style recursive forced deletion"}
```

## Test

```bash
python destructive-bash-hook/tests/test_pre_tool_use_guard.py
```
