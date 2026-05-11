# Destructive Bash Command Blocker Hook

A Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with:

- UTC timestamp
- matched rule
- attempted command
- project path

## Install in 2 commands

From this repository:

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
```

Add the hook to your Claude Code settings:

```json
{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"python3 ~/.claude/hooks/block_destructive_bash.py"}]}]}}
```

If your environment uses `python` instead of `python3`, replace `python3` in the command.

## Expected behavior

Normal commands exit `0` and do not interfere with Claude Code.

Blocked commands exit non-zero, write a clear explanation to stderr, and log the attempt:

```text
Blocked destructive Bash command.
Rule: rm -rf
Reason: Recursive forced removal is blocked because it can delete large parts of the project or filesystem.
Project: /path/to/project
Log: /home/user/.claude/hooks/blocked.log
```

## Local test

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf build","cwd":"/tmp/demo"}}' | python3 hooks/block_destructive_bash.py
```

Expected result: command is blocked and `~/.claude/hooks/blocked.log` receives one JSON line.
