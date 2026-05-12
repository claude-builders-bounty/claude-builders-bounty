# Destructive Bash Command Blocker

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## Install

```bash
python hooks/destructive-command-blocker/install.py
```

The installer copies the hook to `~/.claude/hooks/block_destructive_bash.py` and updates `~/.claude/settings.json`.

## Blocked Patterns

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

## Logging

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log row contains:

- timestamp
- reason
- project path
- attempted command

## Behavior

Normal Bash commands exit with code `0` and continue.

Blocked Bash commands exit with code `2`, which tells Claude Code to block the tool call and show the message from stderr to Claude.

## Quick Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/example"},"cwd":"/tmp/project"}' | python hooks/destructive-command-blocker/block_destructive_bash.py
```
