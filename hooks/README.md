# PreToolUse Dangerous Command Guard

Claude Code `PreToolUse` hook that blocks destructive Bash commands before execution.

## Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line contains timestamp, project path, block reason, and attempted command.

## Install

```bash
bash hooks/install-pretooluse-guard.sh
```

## Manual test

```bash
echo '{"tool_name":"Bash","cwd":"/tmp/project","tool_input":{"command":"rm -rf dist"}}' | ~/.claude/hooks/pre_tool_use_guard.py
```

Expected result: the hook exits with code `2`, logs the attempt, and prints a clear block reason to stderr.

## Test suite

```bash
bash hooks/test-pretooluse-guard.sh
```

The test suite verifies allowed commands, required blocked patterns, and creation of `~/.claude/hooks/blocked.log`.
