# Claude Code Safety Hook: Destructive Command Interceptor

A zero-dependency `pre-tool-use` hook for Claude Code that prevents accidental execution of dangerous shell commands.

## Features & Blocked Patterns
- 🚫 **Recursive Force Deletions**: Intercepts `rm -rf`, `rm -fr`, and flag combinations (`sudo rm -r -f`).
- 🚫 **Database Destruction**: Intercepts `DROP TABLE` and `TRUNCATE TABLE`.
- 🚫 **Unbounded Deletes**: Intercepts `DELETE FROM <table>` without an explicit `WHERE` clause (safe `WHERE` queries pass through).
- 🚫 **Git History Overwrite**: Intercepts `git push --force`, `-f`, and `--force-with-lease`.
- 📝 **Structured Audit Logging**: Automatically appends blocked violations with UTC timestamps to `~/.claude/hooks/blocked.log`.
- ⚡ **Zero Friction**: Standard development commands (`npm`, `git`, `pytest`, `cargo`, `ls`) run with zero overhead.

---

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre-tool-use.py -o ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

---

## Testing & Verification

Run the automated test suite:
```bash
python test_hook.py
```

Output:
```
.......
----------------------------------------------------------------------
Ran 7 tests in 1.943s

OK
```

## Audit Log Example (`~/.claude/hooks/blocked.log`)
```
[2026-09-12T01:19:35.123456+00:00] BLOCKED_RULE=RM_RF | PROJECT=/workspace/backend | CMD="rm -rf /"
[2026-09-12T01:19:35.456789+00:00] BLOCKED_RULE=SQL_DROP_TABLE | PROJECT=/workspace/db | CMD="DROP TABLE users;"
```
