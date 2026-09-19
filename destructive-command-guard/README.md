# Claude Code destructive-command guard

This repository contains a small Python `PreToolUse` hook that blocks the
destructive shell-command patterns listed in bounty issue #3 and records every
blocked attempt in `~/.claude/hooks/blocked.log`.

## Install

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use_guard.py ~/.claude/hooks/
```

Add this hook to the `PreToolUse` handlers for the `Bash` tool in your Claude
Code settings. The hook reads the standard JSON event on stdin, allows safe
commands with exit code 0, and denies dangerous commands with exit code 2 and
a JSON explanation.

## Verify

```bash
python3 -m pytest -q
```

The guard blocks `rm -rf`, `DROP TABLE`, forced `git push`, `TRUNCATE`, and
`DELETE FROM` statements that have no `WHERE` clause. It logs the UTC timestamp,
project path, and attempted command for each block.
