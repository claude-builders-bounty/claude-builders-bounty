## Summary
This PR changes 28 file(s) with approximately 1508 added and 28 removed lines. The fallback reviewer summarizes only signals visible in the diff and does not infer unobserved runtime behavior.

## Risks
- Diff contains credential-sensitive terms; verify no secret material is committed.
- Large change surface increases review risk; consider splitting or adding targeted tests.

## Improvement suggestions
- Call out cross-file behavior changes in the PR description to make verification easier.

## Confidence
Medium
