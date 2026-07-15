# Destructive Command Guard

Claude Code `pre-tool-use` hook that blocks dangerous Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp destructive_command_guard.py ~/.claude/hooks/destructive_command_guard.py
chmod +x ~/.claude/hooks/destructive_command_guard.py
```

Register it in your Claude Code hook config as a `pre-tool-use` hook for Bash.

## What It Blocks

- `rm -rf` style recursive forced deletion
- `git push --force` and `git push --force-with-lease`
- `DROP TABLE`
- `TRUNCATE` / `TRUNCATE TABLE`
- `DELETE FROM` statements without a `WHERE` clause

Normal Bash commands pass through unchanged with exit code `0`.
Blocked attempts exit with code `2`, print a clear message for Claude, and append a tab-separated audit line to:

```text
~/.claude/hooks/blocked.log
```

Each log entry includes timestamp, project path, blocked reason, and attempted command.

## Example Event

```bash
printf '{"tool_input":{"command":"rm -rf .next"},"cwd":"'$PWD'"}' \
  | ~/.claude/hooks/destructive_command_guard.py
```

