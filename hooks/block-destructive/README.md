# Block Destructive Bash Commands

`pre-tool-use.py` is a Claude Code `PreToolUse` hook that denies obviously destructive Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

Add the `hooks/block-destructive/hooks.json` snippet to your Claude Code settings.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`
- `DELETE FROM` without a `WHERE` clause

## What it logs

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with:

- `timestamp`
- `command`
- `project_path`
- `reason`

## Behavior

- Returns a `PreToolUse` deny decision with a clear explanation for Claude Code
- Leaves normal Bash commands untouched
- Accepts both `tool_input.command` and `tool_input.cmd`
