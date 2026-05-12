# Verification

This submission implements a Claude Code `PreToolUse` hook for Issue #3.

## Acceptance checklist

- Hook follows current Claude Code hook format with a `PreToolUse` event and `Bash` matcher.
- Blocks `rm -rf` style recursive force delete commands.
- Blocks `DROP TABLE`.
- Blocks `git push --force`, `git push -f`, and `git push --force-with-lease`.
- Blocks `TRUNCATE`.
- Blocks `DELETE FROM` without a `WHERE` clause.
- Logs every blocked attempt to `~/.claude/hooks/blocked.log`.
- Log entries include timestamp, attempted command, project path, matched rule, and reason.
- Returns a clear `permissionDecision: "deny"` reason to Claude.
- Allows normal Bash commands and passive text inspection.
- README installation is 2 commands.

## Local test command

```bash
cd submissions/duct-tape2/destructive-bash-hook
python3 -m unittest tests/test_block_destructive_bash.py
```

## Expected test coverage

- Required destructive patterns are blocked.
- Safe shell commands are allowed.
- `DELETE FROM ... WHERE ...` is allowed.
- Passive examples such as `echo "DROP TABLE users"` and `grep "DELETE FROM"` are allowed.
- Non-Bash tool calls are ignored.
- Malformed JSON input is handled safely without blocking or crashing.
