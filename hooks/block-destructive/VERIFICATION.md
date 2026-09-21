# VERIFICATION — block-destructive PreToolUse hook

**PR:** https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4404  
**Issue:** #3 ($100)  
**Checked:** 2026-09-22 ~03:35 Asia/Taipei (CST)

## Offline test suite

```bash
python3 hooks/block-destructive/tests/test_patterns.py
```

Expected: every required destructive pattern **denied**, safe commands **allowed**,
`blocked.log` TSV shape = `timestamp\\trule\\tcommand\\tproject_path`.

### Cases covered (expanded overnight)

| Class | Examples |
|-------|----------|
| Block `rm -rf` / wrappers | `rm -rf /tmp/x`, `sudo rm -rf …`, `echo hi && rm -rf build`, `env rm -rf dist` |
| Block SQL | `DROP TABLE`, `TRUNCATE`, unconditional `DELETE FROM` |
| Block force-push | `git push --force`, `-f`, `--force-with-lease` |
| Allow safe | `rm file.txt`, `rm -f single.txt`, `git push origin main`, `DELETE … WHERE …` |
| Non-Bash tools | `tool_name=Read` → pass-through (no deny) |
| Empty / malformed | empty stdin / bad JSON → exit 0 |

## Acceptance checklist (bounty #3)

- [x] Claude Code `~/.claude/hooks/` format (`install.sh` + `settings.json`)
- [x] Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- [x] Logs timestamp + command + project path to `~/.claude/hooks/blocked.log`
- [x] Clear `permissionDecisionReason` for Claude
- [x] Does not interfere with normal Bash (allow tests)
- [x] README install in ≤2 commands

## Notes

- Stdlib-only Python 3 — no pip deps.
- Intentional: a Bash string that literally contains `DROP TABLE` is denied even inside `echo` (prefer false positive over missed SQL drop).
- Maintainer merge still required for Opire Stripe pay; this file is evidence only.
