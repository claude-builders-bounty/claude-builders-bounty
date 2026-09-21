# Acceptance checklist — Bounty #3 ($100)

Hook: `hooks/block-destructive/` · PR: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4404

## Bounty requirements

- [x] Installs into Claude Code hooks (`install.sh` + `settings.json` / project settings)
- [x] Blocks destructive Bash: `rm -rf`, force-push, `DROP TABLE` / `TRUNCATE`, `DELETE FROM` without `WHERE`
- [x] Writes `~/.claude/hooks/blocked.log` with timestamp, rule, command, project path
- [x] Returns a clear `permissionDecisionReason` when denying
- [x] Does not block ordinary safe Bash (covered by allow tests)
- [x] README install path ≤ 2 commands

## How to verify offline

```bash
python3 hooks/block-destructive/tests/test_patterns.py
```

See also `VERIFICATION.md` for the expanded overnight case matrix.

## Scope note

Stdlib-only Python 3. Maintainer merge still required before any Opire/Stripe payout.
