## Summary
- Adds a Python Claude Code `PreToolUse` hook that blocks destructive Bash commands before execution.
- Blocks `rm -rf`, `git push --force` / `git push -f`, `DROP TABLE`, `TRUNCATE`, and `DELETE FROM` without `WHERE`.
- Logs blocked attempts to `~/.claude/hooks/blocked.log` with timestamp, project path, reason, and command.
- Documents two-command installation in the README.

## Test Plan
- `python3 -m unittest tests/test_hook.py -v`
- `python3 -m py_compile claude_destructive_command_hook.py tests/test_hook.py`

## Bounty
Closes #3
