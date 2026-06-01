## Summary

Adds a Claude Code `PreToolUse` hook that blocks destructive Bash commands before execution.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

## Logging

Blocked attempts are appended to:

```text
~/.claude/hooks/blocked.log
```

Each line includes timestamp, project path, block reason, and attempted command.

## Test evidence

Automated tests were run with:

```text
bash hooks/test-pretooluse-guard.sh
```

Expected/observed results:

```text
git status --short                       -> exit 0
rm -rf dist                              -> exit 2
rm -fr dist                              -> exit 2
DROP TABLE users                         -> exit 2
git push --force origin main             -> exit 2
git push --force-with-lease origin main  -> exit 2
TRUNCATE sessions                        -> exit 2
DELETE FROM users;                       -> exit 2
DELETE FROM users WHERE id=1;            -> exit 0
blocked attempts                         -> logged
```

## Checklist

- [x] Follows Claude Code `PreToolUse` hook input format
- [x] Blocks required destructive patterns
- [x] Logs every blocked attempt to `~/.claude/hooks/blocked.log`
- [x] Shows a clear message explaining why the command was blocked
- [x] Allows normal Bash commands
- [x] README includes installation in one command
