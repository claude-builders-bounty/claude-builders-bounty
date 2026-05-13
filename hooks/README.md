# Destructive Bash Command Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

From this repository:

```bash
python3 hooks/install_block_destructive_bash.py
```

Restart Claude Code or run `/hooks` to confirm the `PreToolUse` Bash hook is loaded.

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are logged to:

```text
~/.claude/hooks/blocked.log
```

Each log line is JSON with:

- `timestamp`
- `attempted_command`
- `project_path`
- `reason`

## Hook Behavior

The hook reads Claude Code hook JSON from stdin. For Bash tool calls, it inspects `tool_input.command`.

When a command is blocked, it returns a Claude Code `PreToolUse` denial:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Destructive command blocked"
  }
}
```

Safe Bash commands exit normally without output, so normal commands are not interrupted.

## Test

```bash
python3 -m unittest discover -s tests
```
