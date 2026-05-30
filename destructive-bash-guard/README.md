# Destructive Bash Guard

A Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

From this repository:

```bash
python3 destructive-bash-guard/install.py
```

The installer copies `block_destructive_bash.py` to `~/.claude/hooks/` and adds a `PreToolUse` entry for the Bash tool in `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` and `rm -fr`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Normal Bash commands exit silently with no output and do not interfere with Claude Code.

## Blocked Attempt Log

Every blocked attempt is appended as JSON Lines to:

```text
~/.claude/hooks/blocked.log
```

Each entry includes:

- UTC timestamp
- attempted command
- project path
- blocking reason

## Manual Smoke Test

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"/tmp/project"}\n' | ~/.claude/hooks/block_destructive_bash.py
```

The hook returns a Claude Code `PreToolUse` denial with `permissionDecision: "deny"` and writes the blocked command to `blocked.log`.

## Unit Tests

```bash
python3 destructive-bash-guard/test_block_destructive_bash.py
```
