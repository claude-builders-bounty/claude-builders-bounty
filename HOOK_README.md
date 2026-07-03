# Destructive Bash Command Hook

A Claude Code `pre-tool-use` hook that blocks high-risk shell commands before they run.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
```

```bash
python3 ~/.claude/hooks/block_destructive_bash.py < sample_payloads/rm_rf.json
```

Wire the script into Claude Code as a `pre-tool-use` hook for bash/shell tools.

## What it blocks

- `rm -rf` and common combined flag variants.
- `DROP TABLE`.
- `git push --force` and `git push --force-with-lease`.
- `TRUNCATE`.
- `DELETE FROM ...` statements that do not include a `WHERE` clause.

## Logging

Every blocked command is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line is JSON with:

- UTC timestamp
- attempted command
- project path
- block reason

## Normal commands

Safe shell commands exit with status `0` and produce no output, so normal Claude Code bash usage is not interrupted.
