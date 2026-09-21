# Destructive-command PreToolUse hook

Install in two commands:

```bash
cp -R .claude /path/to/project/
chmod +x /path/to/project/.claude/hooks/block_destructive.py
```

The hook follows the current Claude Code `PreToolUse` JSON contract. It denies `rm -rf`, `DROP TABLE`, `git push --force`/`--force-with-lease`/`-f`, `TRUNCATE`, and any `DELETE FROM` statement without a `WHERE`. Blocked attempts are appended to `~/.claude/hooks/blocked.log` with UTC timestamp, project path, rule, and command. Safe commands produce no output and leave normal permission flow unchanged.

Run `python3 test_hook.py` for offline regression coverage.
