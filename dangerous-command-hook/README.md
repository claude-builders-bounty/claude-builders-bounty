# Dangerous Bash Command Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

1. Copy `.claude/settings.json` and `.claude/hooks/block_dangerous_bash.py` into your project root.
2. Run `chmod +x .claude/hooks/block_dangerous_bash.py`.

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Normal Bash commands are allowed without output.

## How It Works

The project settings file registers a Claude Code `PreToolUse` hook for the `Bash` tool. Claude Code sends the tool call JSON to the Python script on stdin. The script reads `tool_input.command`, checks it against destructive patterns, and returns a structured `permissionDecision: "deny"` response when a command should be blocked.

Every blocked command is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line includes a UTC timestamp, project path, matched rule, and attempted command.

## Test

```bash
python3 test_block_dangerous_bash.py
```
