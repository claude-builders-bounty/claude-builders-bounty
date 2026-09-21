## Claude Code PR Review

> **PR:** [psf/requests#6991](https://github.com/psf/requests/pull/6991) — Fix: Correct Digest Auth URI handling for semicolons in path (#6990)

### Summary
This PR changes src/requests/auth.py, tests/test1.py, with approximately 41 added and 2 removed lines. The main intent appears to be: Fix: Correct Digest Auth URI handling for semicolons in path (#6990). The review below focuses on regression risk, test coverage, and maintainability visible from the diff.

### Identified Risks
- The diff touches authentication or security-sensitive behavior; regressions could affect request integrity or access control.

### Improvement Suggestions
- Add focused regression tests for malformed, empty, and boundary inputs around the security-sensitive path.

### Confidence: High
