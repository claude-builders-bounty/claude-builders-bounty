# Submission draft — bounty issue #3

## Proposed PR title

Add deterministic PreToolUse guard for destructive Bash commands

## Summary

This change adds a small, dependency-free Python `PreToolUse` hook that blocks
the destructive Bash patterns listed in issue #3:

- recursive/forced `rm`
- forced Git pushes
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

It writes one JSON audit record per blocked attempt, emits a Claude Code deny
decision with a clear remediation message, and leaves read-only commands alone.

## Files

- `hooks/block-destructive-bash.py`
- `hooks/install.sh`
- `hooks/settings.example.json`
- `hooks/README.md`
- `hooks/tests/test_block_destructive_bash.py`

## Validation

- `python -m unittest discover -s hooks/tests -v` — 10 tests passed
- `python -m py_compile hooks/block-destructive-bash.py hooks/tests/test_block_destructive_bash.py` — passed
- `bash -n hooks/install.sh` — passed
- `git diff --check` — passed

## Claim and submission steps

1. Comment `/opire try` on issue #3.
2. Push the local branch `bounty-3-block-destructive-bash` to a fork.
3. Open a pull request using the repository's normal PR flow.
4. Do not state that the bounty is earned until the PR is merged and the
   platform confirms payment.

This draft is intentionally not posted or sent.
