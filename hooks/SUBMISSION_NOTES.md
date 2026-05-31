# Submission Notes

Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

## Summary

This package adds a Claude Code pre-tool-use hook that blocks destructive bash and SQL commands before execution.

It blocks:

- `rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force` and `git push -f`
- `DELETE FROM ...` without a `WHERE` clause

Blocked attempts are logged as JSON Lines to `~/.claude/hooks/blocked.log` with timestamp, attempted command, project path, and matched rule.

## Verification

```powershell
python -m py_compile .\hooks\block_destructive_commands.py .\hooks\test_block_destructive_commands.py
python .\hooks\test_block_destructive_commands.py
```

All commands passed locally.

## Files

- `hooks/block_destructive_commands.py`
- `hooks/test_block_destructive_commands.py`
- `hooks/README.md`
