# Claude Code PreToolUse Hook: Block Destructive Commands

A security hook for Claude Code that intercepts and blocks dangerous shell commands before they execute.

## What it blocks
* `rm -rf` / `rm --recursive --force`
* `DROP TABLE`
* `git push --force` / `git push -f`
* `TRUNCATE`
* `DELETE FROM ...` (without a `WHERE` clause)

Blocked commands are logged to `~/.claude/hooks/blocked.log` with a timestamp and the working directory.

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp block-destructive.py ~/.claude/hooks/
claude hook add --event pre-tool-use --script ~/.claude/hooks/block-destructive.py
```
