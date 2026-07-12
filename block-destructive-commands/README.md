# Block Destructive Commands Hook

This is a Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before they are executed.

## Features
- Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause.
- Logs all blocked attempts to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.
- Displays a clear message explaining why the command was blocked.
- Does not interfere with normal bash commands.

## Installation (in 2 commands)

You can easily install this hook by downloading it and running it with the `--install` flag:

```bash
curl -sO https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/block-destructive-commands/hook.py
python3 hook.py --install
```

This will automatically:
1. Copy the hook script to `~/.claude/hooks/block_destructive.py` and make it executable.
2. Update your `~/.claude/settings.json` to register the `PreToolUse` hook for Bash commands.

## Requirements
- Python 3.x

## How it works

When Claude Code attempts to run a bash command, this hook receives the context as JSON via `stdin`. If any of the dangerous patterns are detected, the hook exits with a non-zero status code, which blocks the tool execution. The output error is sent back to Claude explaining exactly why it was blocked.
