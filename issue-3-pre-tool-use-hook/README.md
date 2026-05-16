# Pre-tool-use Hook: Block Destructive Bash Commands

This hook blocks risky commands before execution in Claude Code.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use_guard.py ~/.claude/hooks/pre_tool_use_guard.py
chmod +x ~/.claude/hooks/pre_tool_use_guard.py
```

Then configure Claude Code to run this script as a `pre-tool-use` hook.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

## Logging

Blocked attempts are appended to:

`~/.claude/hooks/blocked.log`

Each log line includes:

- timestamp (UTC)
- project path (current working directory)
- attempted command
- block reason

## Behavior

- Normal commands are allowed.
- Blocked commands return a clear explanatory message and non-zero exit code.
