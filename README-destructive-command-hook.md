# Destructive Command Hook

`destructive_command_hook.py` is a Claude Code pre-tool-use hook that blocks high-risk shell commands before they execute.

## Install

```bash
mkdir -p ~/.claude/hooks && cp destructive_command_hook.py ~/.claude/hooks/pre_tool_use.py
chmod +x ~/.claude/hooks/pre_tool_use.py
```

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are appended to:

```text
~/.claude/hooks/blocked.log
```

Each log entry includes the UTC timestamp, reason, project path, and attempted command.

## Behavior

The hook accepts either plain command text or a JSON payload from Claude Code. It looks for command values in common payload shapes such as:

- `command`
- `input.command`
- `tool_input.command`
- `parameters.command`

Safe commands exit with status `0`. Blocked commands exit with status `2` and print a clear explanation to stderr.

## Local Checks

```bash
python destructive_command_hook.py "echo hello"
python destructive_command_hook.py "rm -rf build"
python destructive_command_hook.py '{"command":"DELETE FROM users"}'
python destructive_command_hook.py '{"command":"DELETE FROM users WHERE id = 1"}'
```

The first and last commands pass. The destructive examples are blocked and logged.
