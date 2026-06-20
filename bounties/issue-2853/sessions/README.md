# Issue #2853 verification session diffs

`tests/verify-issue-2853.sh` archives working-tree patches here before and after each
verification phase (`start`, `post-npm-test`, `complete`, or `failed`). Committed patches
let reviewers inspect successful and failed takeover attempts without re-running CI.

Patches are named `session-<timestamp>-<label>-<phase>.patch`.
