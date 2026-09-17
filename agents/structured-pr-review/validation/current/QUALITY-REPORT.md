# Current reviewer accuracy validation

This follow-up repairs the concrete errors disclosed in the earlier draft. It
uses actual authenticated Claude Code with its `opus` profile, not the earlier
small local-model substitution. Models remain configurable; this validates the
recorded configuration, not every backend or every future model alias.

## Evidence

- 79 deterministic tests pass, covering exact before/after source references,
  full-line quotes, atomic audit fields, changed-guard causality, bounded hunk
  partitioning, Python AST syntax facts, error preservation and native CLI flags.
- Three complete native CLI runs on public Click PRs #3860, #3782 and #3866
  succeeded. Their exact pinned input packets and model outputs are retained.
  The known tuple/scalar, missing-Windows-tests, release-heading and wrapping-test
  recommendations do not appear in these final outputs.
- The larger #3866 diff was processed in eight groups with sixteen model calls,
  completing in 387.7 seconds under a 240-second per-call timeout. This is not a
  240-second total-runtime claim or an interactive-latency guarantee.
- Native positive controls retained the genuine empty-input division failure
  and the first invalid array index. A tuple negative control did not produce
  the former false scalar-return finding.
- Six additional held-out fixture expectations were fixed before model execution:
  three introduced defects (missing-key lookup, zero timeout, dropped final item)
  and three intentional/safe changes. All six defect-presence checks matched.
- A real CLI run using the shipped default model/budget also succeeded on #3782.

## Interpretation and limits

Across the nine synthetic controls there were five positive and four negative
cases; all expected presence/absence verdicts matched. That small regression set
is not a calibrated general accuracy benchmark. Three real-PR reviews establish
completion and source fidelity on those particular diffs, not absence of all bugs.
The held-out timeout finding correctly identifies that 0 becomes 500, but its
extra wording that a caller 'waits 500 units' extrapolates beyond the helper itself.
We retain that wording in the unedited output rather than claiming perfect prose.

Source quoting is provenance, not proof. The independent audit checks the actual
statement, scenario, fix, and whether a defect is introduced. Complete Python
expressions are also checked syntactically where available. Confidence is capped
at Medium and lowered for incomplete contexts. Failures are visible; a timeout
never becomes a fabricated clean review. No generated comment was posted on the
sample upstream PRs. Human review remains appropriate before publishing findings.

Earlier local-model failures and raw samples remain in this PR. A default profile
that clears these regressions is supplied, while small local alternatives remain
explicitly experimental. Maintainer acceptance and reward eligibility are separate.
