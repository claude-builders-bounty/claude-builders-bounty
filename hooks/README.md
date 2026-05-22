# Destructive Bash Command Hook

This PreToolUse hook blocks high-risk Bash commands before Claude Code runs them.

## Install

```bash
python hooks/install.py
```

The installer copies `block-dangerous-bash.py` into `~/.claude/hooks/` and adds it to `~/.claude/settings.json` under `PreToolUse` for the `Bash` tool.

## What It Blocks

- `rm -rf` and equivalent recursive forced remove flags
- `git push --force` and `git push --force-with-lease`
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- SQL `DELETE FROM` statements that do not include `WHERE`

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a UTC timestamp, project path, reason, and attempted command.

## Manual Test

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/example"},"cwd":"/tmp/project"}' | python hooks/block-dangerous-bash.py
```

The hook returns a JSON decision denying the command and writes the attempt to `~/.claude/hooks/blocked.log`.

## Test

```bash
python hooks/test_block_dangerous_bash.py
```
