# Destructive Bash Command Blocker

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## What It Blocks

- `rm -rf` and `rm -fr`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with:

- timestamp
- attempted command
- project path
- block reason

## Install

Run from this repository:

```bash
python3 hooks/install_block_destructive_bash.py
```

Then run `/hooks` in Claude Code and confirm a `PreToolUse` hook is registered for `Bash`.

## Manual Configuration

If you prefer manual setup, copy `hooks/block_destructive_bash.py` into `~/.claude/hooks/` and add the contents of `hooks/settings.example.json` to `~/.claude/settings.json`.

## Behavior

Safe Bash commands pass silently and do not write to the log. Blocked commands return a Claude Code `PreToolUse` denial with a clear reason so Claude can choose a safer, reversible command or ask the user for confirmation.

## Test

```bash
python3 -m unittest tests/test_block_destructive_bash.py
```
