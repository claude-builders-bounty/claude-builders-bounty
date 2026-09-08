## Summary
Implements issue #3: a Claude Code PreToolUse hook that intercepts destructive bash/SQL before execution.

Closes #3

## Acceptance
- [x] Hook follows Claude Code hooks format (`hooks/block-destructive.py` + `hooks/install.sh`)
- [x] Blocks recursive force-delete, schema-drop, `git push --force` / `-f`, unscoped wipe, and unscoped row-delete
- [x] Logs timestamp, command, and project path to `~/.claude/hooks/blocked.log`
- [x] Clear stderr + JSON deny decision for Claude (exit 2)
- [x] Does not interfere with normal bash
- [x] README install in 2 commands

## Test
```bash
python3 tests/test_block_destructive.py
```
