# Destructive Bash Guard Hook

Claude Code `PreToolUse` hook for Bash that blocks high-risk destructive commands before they run.

## What It Blocks

- `rm -rf` and `rm -fr` style recursive force deletes
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- SQL `DELETE FROM ...` statements that do not include a `WHERE` clause

Every blocked command is logged to `~/.claude/hooks/blocked.log` as JSON Lines with:

- UTC timestamp
- attempted command
- project path
- block reason

## Install

Run these two commands from this directory:

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive_bash_guard.py ~/.claude/hooks/destructive_bash_guard.py && chmod +x ~/.claude/hooks/destructive_bash_guard.py
python3 hooks/install_destructive_bash_guard.py
```

The installer safely adds this hook to `~/.claude/settings.json` under `PreToolUse` with matcher `Bash`. Existing hooks are preserved.

## Test

```bash
python3 tests/test_destructive_bash_guard.py
```

## How It Works

Claude Code sends hook input as JSON on stdin. For Bash calls, this hook reads `tool_input.command`, checks it against destructive patterns, and exits with code `2` when a command should be blocked. Claude Code treats exit code `2` from `PreToolUse` hooks as a blocking error and feeds stderr back to Claude, so the model can explain the reason and choose a safer command.

Safe commands exit `0` with no output, so normal Bash usage is not affected.
