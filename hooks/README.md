# Claude Code destructive command blocker

A Claude Code `pre-tool-use` hook that blocks dangerous Bash commands before execution.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use_blocker.py ~/.claude/hooks/pre_tool_use_blocker.py
chmod +x ~/.claude/hooks/pre_tool_use_blocker.py
```

Then register `~/.claude/hooks/pre_tool_use_blocker.py` as a `pre-tool-use` hook in your Claude Code hooks configuration.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with:

- UTC timestamp
- attempted command
- project path
- block reason

Normal Bash commands and non-Bash tool calls exit successfully and are not logged.
