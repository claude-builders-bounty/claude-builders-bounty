# PR Notes

Closes #3.

## What Changed

- Added a Claude Code `PreToolUse` Bash hook at `hooks/block-dangerous-bash.py`.
- Added `install.sh` to copy the hook into `~/.claude/hooks/` and update `~/.claude/settings.json`.
- Added `settings.example.json` showing the hook configuration.
- Added tests that prove required destructive patterns are blocked and normal commands are silent.

## Acceptance Criteria

- Hook follows Claude Code hooks format with a `PreToolUse` / `Bash` matcher.
- Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without `WHERE`.
- Logs blocked attempts to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.
- Displays a clear deny reason to Claude through `permissionDecisionReason`.
- Normal Bash commands do not produce hook output.
- README install is two commands.
