# Destructive Bash Guard Hook

Claude Code `PreToolUse` hook that blocks high-risk Bash commands before execution.

## Install

```bash
python hooks/destructive-bash-guard/install.py
```

The installer copies the hook to `~/.claude/hooks/block_destructive_bash.py` and adds a `PreToolUse` entry for the `Bash` tool in `~/.claude/settings.json`.

## What It Blocks

- `rm` commands that combine recursive and force flags, such as `rm -rf dist`.
- SQL statements containing `DROP TABLE`.
- SQL statements containing `TRUNCATE`.
- `DELETE FROM ...` statements that do not include a `WHERE` clause.
- `git push --force` and `git push --force-with-lease`.

Normal Bash commands pass through unchanged.

## Blocked Attempt Log

Every blocked command is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line is JSON with:

- `timestamp`
- `attempted_command`
- `project_path`
- `reason`

## Hook Behavior

Claude Code sends hook payload JSON on stdin. The hook reads `tool_input.command`, evaluates it, and returns:

- exit code `0` for allowed commands
- exit code `2` with a clear stderr explanation for blocked commands

Use `CLAUDE_HOOKS_BLOCKED_LOG=/tmp/blocked.log` during tests to redirect the log file.
