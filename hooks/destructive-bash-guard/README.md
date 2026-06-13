# Destructive Bash Guard

Claude Code `pre-tool-use` hook that blocks dangerous Bash commands before execution.

## Install

```bash
python hooks/destructive-bash-guard/pre_tool_use.py --install
```

Restart Claude Code after installation.

## What It Blocks

- `rm -rf` and `rm -fr`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

## Logging

Every blocked command is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line includes timestamp, project path, reason, and the attempted command.

## Manual Test

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/demo"},"cwd":"/tmp/project"}' | python hooks/destructive-bash-guard/pre_tool_use.py
```

Expected result: exit code `2`, a clear block message on stderr, and a new entry in `~/.claude/hooks/blocked.log`.
