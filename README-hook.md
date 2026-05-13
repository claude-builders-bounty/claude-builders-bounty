# Claude Code destructive command blocker

This is a Claude Code `pre-tool-use` hook that blocks high-risk Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use_blocker.py ~/.claude/hooks/pre_tool_use_blocker.py && chmod +x ~/.claude/hooks/pre_tool_use_blocker.py
```

```bash
claude config set hooks.pre_tool_use ~/.claude/hooks/pre_tool_use_blocker.py
```

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line is JSON and includes:

- timestamp
- attempted command
- project path
- block reason

## Behavior

The hook reads the Claude Code hook JSON payload from `stdin`, finds the attempted Bash command, and exits successfully for normal commands. For blocked commands it prints a clear error message to `stderr`, logs the attempt, and exits with status `2` so Claude Code stops the tool call.

## Quick local test

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/example"}}' | python3 hooks/pre_tool_use_blocker.py
```

Expected: command is blocked and a log entry is written.

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 hooks/pre_tool_use_blocker.py
```

Expected: exits `0` and does not log anything.
