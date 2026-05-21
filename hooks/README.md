# Destructive Bash Command Guard

A Claude Code `PreToolUse` hook for the `Bash` tool that blocks common destructive shell and SQL commands before they run.

## Install

macOS/Linux:

```sh
python3 hooks/install_block_destructive_hook.py
```

Windows:

```powershell
py hooks\install_block_destructive_hook.py
```

The installer copies `block_destructive_bash.py` into `~/.claude/hooks/` and adds a `PreToolUse` matcher for `Bash` in `~/.claude/settings.json`.

## What It Blocks

- `rm -rf`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Allowed Bash commands exit with code `0` and produce no output. Blocked commands exit with code `2` and print a clear message to `stderr`, which matches Claude Code's documented hook blocking behavior.

## Logging

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log entry is JSON Lines format and includes:

- UTC timestamp
- attempted command
- project path
- block reason

## Test

```sh
python3 -m unittest discover -s tests -v
```
