# Claude Code destructive-command PreToolUse hook

Blocks dangerous Bash commands before execution while allowing ordinary Bash commands to continue normally.

## Install

1. Run `python3 install.py` from this directory.
2. Restart Claude Code (or start a new session) so the updated hook configuration is loaded.

The installer copies the hook to `~/.claude/hooks/pre-tool-use.py` and merges one `PreToolUse` matcher for `Bash` into `~/.claude/settings.json` without replacing unrelated settings.

## Blocked patterns

- `rm -rf` (including common `-fr` / split `-r -f` forms)
- `DROP TABLE`
- `git push --force` (also `-f` and `--force-with-lease`)
- `TRUNCATE`
- `DELETE FROM` when that SQL statement has no `WHERE` clause

Matching is case-insensitive where applicable. A safe statement such as `DELETE FROM users WHERE id = 7` is allowed.

## Audit log

Every blocked attempt is appended as one JSON line to `~/.claude/hooks/blocked.log` with:

- UTC timestamp
- attempted command
- project path from Claude Code's hook input (`cwd`)
- block reason

The hook writes a clear denial reason to stderr and exits with code `2`, which blocks a `PreToolUse` tool call. Safe commands exit `0` with no output.

## Verify

Run `python3 tests/test_hook.py` to exercise destructive commands, safe commands, logging, invalid-input fail-closed behavior, and installer idempotency in a temporary HOME. The tests do not modify your real `~/.claude` directory.
