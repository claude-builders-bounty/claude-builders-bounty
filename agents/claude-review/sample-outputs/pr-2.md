<!-- PR: https://github.com/psf/requests/pull/7128
Run: ./claude-review --pr https://github.com/psf/requests/pull/7128 --snapshot sample-outputs/evidence/pr-2.json
Evidence: read-only GitHub connector fetch_pr_patch, 2026-10-11. Python network blocked; actual patches replayed locally.
-->

# PR review: fix: handle empty string cookie values correctly

PR: https://github.com/psf/requests/pull/7128
Head: a3d9a050e7c0e13d1b0ffa4e033bf2016a1f04bf
Source: Read-only GitHub connector fetch\_pr\_patch; per-file unified patches, retrieved 2026-10-11

## Summary of changes

The supplied patches change 2 files: src/requests/cookies.py, tests/test\_requests.py. Observed textual changes contain 9 additions and 1 deletions, including 8 added test lines; this draft uses offline heuristics and does not execute the target code.

## Identified risks

- Security/session-related path changed: src/requests/cookies.py (path signal, not a confirmed defect).

## Improvement suggestions

- Exercise boundary cases and existing security/session tests: src/requests/cookies.py.
- Run the changed tests (8 added test lines observed); test presence does not establish coverage or passing status.

## Confidence

**Med** (Medium abbreviated Med). Confidence concerns the observed heuristic signals, not merge safety; no target tests were run.
