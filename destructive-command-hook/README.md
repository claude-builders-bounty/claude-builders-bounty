# Destructive Bash Command Guard Hook

A Claude Code `pre-tool-use` hook that blocks dangerous bash commands before they run.

It blocks:

- `rm -rf`
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a timestamp, project path, and attempted command.

## Install

```bash
mkdir -p ~/.claude/hooks && cp destructive_bash_guard.py ~/.claude/hooks/destructive_bash_guard.py
chmod +x ~/.claude/hooks/destructive_bash_guard.py
```

Then add it to your Claude Code hooks configuration as a `PreToolUse` hook for Bash tool calls.

## Usage

Claude Code sends hook input as JSON on stdin. The hook reads the bash command from common fields such as:

- `tool_input.command`
- `tool_input.cmd`
- `command`

Safe commands exit with code `0` and do not interfere with execution.

Blocked commands exit with code `2` and print a clear message explaining why the command was blocked.

## Manual test

```bash
printf '{"tool_input":{"command":"rm -rf /tmp/demo"}}' | ~/.claude/hooks/destructive_bash_guard.py
printf '{"tool_input":{"command":"echo safe"}}' | ~/.claude/hooks/destructive_bash_guard.py
```

Expected result:

- The first command is blocked and logged.
- The second command exits successfully.
