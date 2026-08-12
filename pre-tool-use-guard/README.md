# 🔒 pre-tool-use-guard

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code/hooks) `PreToolUse` hook that
**blocks destructive bash commands before they run** — and logs every blocked attempt.

No dependencies. Pure Python 3 stdlib. Works on macOS / Linux / Windows (WSL).

---

## Why

AI agents sometimes run commands that are very hard to undo:

```bash
rm -rf /var/www
git push --force origin main
DROP TABLE users;
TRUNCATE logs;
DELETE FROM sessions;   # no WHERE clause
```

This hook intercepts those patterns at the `PreToolUse` stage, denies them,
tells Claude *why*, and appends a structured entry to `~/.claude/hooks/blocked.log`.
Everything else passes through untouched.

---

## Install (2 commands)

```bash
bash install.sh
# → "installed" + "Done. pre-tool-use-guard is active."
```

That's it — it copies the hook to `~/.claude/hooks/` and registers it in
`~/.claude/settings.json` (idempotent, re-running is safe).

Verify it's live:

```bash
echo '{"session_id":"t","tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"},"cwd":"/tmp","hook_event_name":"PreToolUse"}' | python3 ~/.claude/hooks/pre_tool_use_guard.py
# → {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", ...}}
```

---

## What it blocks

| Pattern | Example | Reason |
|---|---|---|
| Recursive force delete | `rm -rf`, `rm -fr`, `sudo rm -rf /` | `rm -rf (recursive force delete)` |
| Schema drop | `DROP TABLE`, `drop database prod` | `DROP TABLE/DATABASE/SCHEMA/INDEX/VIEW` |
| Force push | `git push --force`, `git push -f` | `git push --force` |
| Table truncation | `TRUNCATE TABLE logs` | `TRUNCATE TABLE` |
| Unscoped delete | `DELETE FROM users` (no `WHERE`) | `DELETE FROM without WHERE clause` |

Safe variants pass through: `rm -f file.txt`, `rm -r backup/`, `git push origin main`,
`DELETE FROM users WHERE id = 5`, `SELECT ...`, etc.

## Logging

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as one JSON line:

```json
{"timestamp": "2026-08-11 01:03:03", "reason": "rm -rf (recursive force delete)", "attempted_command": "sudo rm -rf /", "project_path": "/var/www"}
```

## Test evidence

`test_guard.py` runs the full acceptance matrix — 10 destructive commands must be
denied, 8 safe commands must be allowed, non-Bash tools must pass through:

```
=== must block ===
  [PASS] rm -rf                  -> deny
  [PASS] sudo rm -rf /           -> deny
  [PASS] DROP TABLE              -> deny
  [PASS] git push --force        -> deny
  [PASS] git push -f             -> deny
  [PASS] TRUNCATE                -> deny
  [PASS] DELETE no where         -> deny
  ...
=== must allow ===
  [PASS] rm -f single file       -> allow
  [PASS] rm -r no -f             -> allow
  [PASS] git push normal         -> allow
  [PASS] DELETE with WHERE       -> allow
  ...
✅ all checks pass
```

## Files

| File | Purpose |
|---|---|
| `pre_tool_use_guard.py` | The hook (reads JSON on stdin, writes JSON decision on stdout) |
| `install.sh` | One-command installer + settings.json registration |
| `test_guard.py` | Acceptance test suite |

## License

MIT
