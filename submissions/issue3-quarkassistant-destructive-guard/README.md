# Issue #3 — Claude Code destructive Bash guard

A production-oriented Claude Code `PreToolUse` hook that blocks destructive Bash/SQL commands before they execute, while staying quiet for normal development commands and documentation/search workflows.

## Why this version

Most simple guards use raw substring matching. That catches the required phrases, but it also blocks harmless commands like `grep "DROP TABLE" docs/` or `echo 'rm -rf /' >> safety-notes.md`. This implementation parses the shell command into executable groups first, then applies context-aware checks:

- `rm` is blocked only when recursive **and** forced (`rm -rf`, `rm -fr`, `rm --recursive --force`).
- `git push --force`, `git push -f`, and `--force-with-lease` are blocked.
- SQL is blocked when it appears as actual SQL or in DB-client invocations (`sqlite3`, `psql`, `mysql`, `turso`, etc.).
- `DELETE FROM` is allowed only when the same statement contains a `WHERE` clause.
- Documentation/search commands (`echo`, `printf`, `grep`, `rg`, etc.) are not blocked just because they mention dangerous text.

Blocked attempts are written as JSON lines to `~/.claude/hooks/blocked.log` with:

- UTC timestamp
- attempted command
- project path
- matched rule
- human-readable reason

Claude receives a structured `permissionDecision: "deny"` response for the `PreToolUse` event, matching the current Claude Code hooks format.

## Install — 2 commands

From this directory after cloning the repo:

```bash
mkdir -p ~/.claude/hooks && cp destructive_guard.py ~/.claude/hooks/destructive_guard.py && chmod +x ~/.claude/hooks/destructive_guard.py
python3 ~/.claude/hooks/destructive_guard.py --install-settings
```

The installer merges this hook into `~/.claude/settings.json` without deleting existing hook groups.

## What it blocks

```bash
rm -rf .next/cache
git push --force origin main
sqlite3 app.db 'DROP TABLE users'
psql "$DATABASE_URL" -c 'TRUNCATE audit_log'
DELETE FROM sessions
```

## What it allows

```bash
rm -f ./tmp-file
git push origin feature/my-branch
sqlite3 app.db 'DELETE FROM sessions WHERE expires_at < datetime("now")'
grep -R "DROP TABLE" docs/
echo 'rm -rf /' >> docs/safety.md
```

## Test

```bash
python3 -m unittest submissions/issue3-quarkassistant-destructive-guard/tests/test_destructive_guard.py
python3 -m py_compile submissions/issue3-quarkassistant-destructive-guard/destructive_guard.py submissions/issue3-quarkassistant-destructive-guard/tests/test_destructive_guard.py
```

## Manual hook smoke test

```bash
printf '%s' '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"rm -rf ."},"cwd":"/tmp/demo"}' \
  | CLAUDE_HOOK_LOG=/tmp/blocked.log python3 destructive_guard.py
cat /tmp/blocked.log
```

Expected behavior: stdout contains `permissionDecision: deny`, and `/tmp/blocked.log` contains the attempted command plus project path.

---

AI-assisted: authored by QuarkAssistant using GPT/Codex tooling, with local tests run before submission.
