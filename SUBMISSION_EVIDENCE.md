# Bounty #3 submission evidence

This is a local review aid for the destructive-command PreToolUse hook. It is
not an Opire claim, pull request, or payment request.

## Acceptance criteria mapping

- **Claude Code hook format:** `hooks/install.py` installs the hook under
  `~/.claude/hooks/` and merges the Bash matcher into existing settings.
- **Required destructive patterns:** the guard blocks recursive/forced `rm`,
  `git push --force` variants, `DROP TABLE`, `TRUNCATE`, and `DELETE FROM`
  unless the same SQL statement has a `WHERE` clause.
- **Nested and wrapped commands:** it inspects common shell wrappers,
  substitutions, `eval`, `find -exec`, `xargs`, and command-prefix utilities
  such as `time`, `nice`, `timeout`, and `stdbuf`, with a finite nesting bound.
- **Audit record:** each denial records a UTC timestamp, redacted and
  length-limited command, project path, and reason in
  `~/.claude/hooks/blocked.log`.
- **Clear denial:** the PreToolUse response denies the command and gives Claude
  a reason and safer alternative. Invalid hook input and log-write failure
  fail closed.
- **Benign commands:** dedicated tests cover ordinary commands, scoped SQL
  deletes, and literal or escaped examples.
- **Installation docs:** the root README documents installation with one
  command: `python3 hooks/install.py`.

## Verification

Run from the repository root:

```text
python -m unittest discover -s tests -v
python -m compileall -q hooks tests
```

The standard-library `unittest` command is the runner used by GitHub Actions.
On 2026-09-26, local Windows runs on Python 3.12, 3.13, and 3.14 each ran
**35 tests: 35 passed, 0 failed, 0 skipped**. `compileall` and
`git diff --check` also passed. On commit `9e2c840`, fork GitHub Actions run
`36135703613` succeeded on Windows 2022 and Ubuntu 24.04. The upstream PR's
Checks view currently reports zero checks, so the fork run is not represented
as upstream CI. The tests use temporary settings and logs and do not modify
the user's Claude Code configuration.

## Scope and limitation

The hook is a best-effort command guard, not a complete Bash parser or a
security sandbox. The README documents syntax that can evade heuristic
inspection and false-positive risks; ambiguous or over-nested inputs are
handled conservatively.

As of 2026-09-26, PR #4319 remains open on `bounty3-destructive-hook`; `/claim
#3` has been posted. The PR is not merged, and there is no evidence here of a
reward adjudication or payment. These facts do not imply that the bounty is
guaranteed.
