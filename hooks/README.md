# Destructive Bash command blocker

This adds a Claude Code `PreToolUse` hook for Bash commands. It blocks commands that are easy to run accidentally and hard to recover from, then records the blocked attempt in `~/.claude/hooks/blocked.log`.

## Install

Run these two commands from the repository root:

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use_block_destructive.py ~/.claude/hooks/block-destructive.py && chmod +x ~/.claude/hooks/block-destructive.py
python ~/.claude/hooks/block-destructive.py --install-settings
```

## What it blocks

- `rm -rf` and equivalent recursive force remove flags
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `DELETE FROM ...` without a `WHERE` clause

Normal Bash commands are allowed without extra output.

## Log format

Blocked attempts are written as JSON lines to `~/.claude/hooks/blocked.log` with:

- UTC timestamp
- project path
- matched rule
- attempted command

For tests or custom setups, set `CLAUDE_HOOK_LOG_PATH` to another file path.

## Quick local check

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"/tmp/project"}' | python hooks/pre_tool_use_block_destructive.py
```

The hook exits with code `2` for blocked commands so Claude Code stops the tool call and sees the reason.
