# Bounty #3 — Verification

## Run tests

From the repository root:

```bash
make ci-validate
```

Or from this directory:

```bash
make ci-validate
# equivalent: bash tests/run-ci-checks.sh
```

## Expected output

```
Ran 84 tests in ...s
OK
Ran 13 tests — OK
OK: peer review acceptance tests passed
OK: all CI validation checks passed
```

## Acceptance criteria

- [x] PreToolUse hook in Claude Code format (`~/.claude/hooks/`)
- [x] Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- [x] Logs blocked attempts to `~/.claude/hooks/blocked.log` (timestamp, command, project path)
- [x] Clear denial message via official `hookSpecificOutput` schema
- [x] Safe commands pass through unchanged
- [x] README with 2-command install (`git clone` + `install.sh`)
