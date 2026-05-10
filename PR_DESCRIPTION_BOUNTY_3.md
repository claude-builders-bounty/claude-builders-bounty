# Bounty #3: Destructive Command PreToolUse Hook

## Summary

Implements a Python Claude Code `PreToolUse` hook that blocks destructive Bash commands before execution and logs blocked attempts to `~/.claude/hooks/blocked.log`.

## What changed

- Added `.claude/hooks/block_destructive_commands.py`
  - Reads Claude Code hook JSON from stdin.
  - Only evaluates `Bash` tool calls.
  - Blocks:
    - `rm -rf`
    - `DROP TABLE`
    - `git push --force`
    - `TRUNCATE`
    - `DELETE FROM` without `WHERE`
  - Emits `hookSpecificOutput.permissionDecision = "deny"` for blocked commands.
  - Allows normal Bash commands silently.
- Added `install_destructive_command_hook.py`
  - Copies the hook into `~/.claude/hooks/`.
  - Adds the matching `PreToolUse` hook entry to `~/.claude/settings.json`.
- Added `README-destructive-command-hook.md`
  - Documents behavior, blocked patterns, log format, and one-command installation.
- Added `tests/test_block_destructive_commands.py`
  - Covers blocked command patterns.
  - Covers allowed normal commands.
  - Verifies denied hook output and blocked log contents.

## Acceptance Criteria

- [x] Hook follows Claude Code `PreToolUse` hook format.
- [x] Blocks `rm -rf`.
- [x] Blocks `DROP TABLE`.
- [x] Blocks `git push --force`.
- [x] Blocks `TRUNCATE`.
- [x] Blocks `DELETE FROM` without a `WHERE` clause.
- [x] Logs blocked attempts to `~/.claude/hooks/blocked.log`.
- [x] Log includes timestamp, attempted command, and project path.
- [x] Displays a clear denial reason to Claude.
- [x] Does not interfere with normal Bash commands.
- [x] README installation is one command.

## Test

```powershell
py tests\test_block_destructive_commands.py
```

Result:

```text
All destructive-command hook checks passed.
```

## Notes

The installer records the Python interpreter used to run it, so it works on systems where `python3` is not available but Python is launched another way.
