# PROGRESS.md — Issue #3 Destructive Bash Hook

## Bounty
- Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
- Goal: Add a Claude Code `PreToolUse` hook that blocks destructive Bash commands and logs blocked attempts.

## Completed
- Added `hooks/block_destructive_bash.py` with standard-input Claude hook payload handling.
- Blocks `rm -rf`, `DROP TABLE`, `git push --force` / `git push -f`, `TRUNCATE`, and `DELETE FROM` without `WHERE`.
- Logs blocked attempts to `~/.claude/hooks/blocked.log` with timestamp, command, project path, and reason.
- Added `install-hook.sh` to copy the hook to `~/.claude/hooks/` and merge Claude Code settings automatically.
- Added README installation instructions in two commands.
- Added Python standard-library tests and package scripts for harness commands.

## Verification
- `bash setup.sh` ✅
- `pnpm run type-check` ✅
- `pnpm test` ✅
- `pnpm run lint` ✅
- `pnpm run build` ✅
- Manual hook check with temporary `HOME`: dangerous command exits `2` and writes `blocked.log` ✅
