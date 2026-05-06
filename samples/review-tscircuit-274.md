# Code Review: tscircuit/schematic-trace-solver#274

**PR Title:** fix: remove spurious extra trace lines from duplicate consecutive points (#78)
**URL:** https://github.com/tscircuit/schematic-trace-solver/pull/274
**Reviewer:** Claude Code (claude-sonnet-4-6)
**Date:** 2026-05-06

---

### Summary

This PR removes spurious extra trace lines caused by consecutive duplicate points in trace paths. The root cause is that path splicing in `UntangleTraceSubsolver._applyBestRoute()` and other path functions can produce duplicate boundary points, creating zero-length segments that render as visual artifacts. The fix adds a `removeDuplicateConsecutivePoints()` function and applies it in `simplifyPath()`, plus adds comprehensive tests.

### Identified Risks

- No significant risks identified. The EPS comparison (1e-9) is appropriate for the coordinate space and the function is a pure utility with no side effects. The snapshot updates (12 files) are expected given the bug fix — they represent the corrected output, not regressions.

### Improvement Suggestions

- The `removeDuplicateConsecutivePoints` function could be extracted to a shared utility file if other solvers need duplicate-point deduplication in the future. Currently it lives in `simplifyPath.ts` alongside `simplifyPath`, which is acceptable for now but worth watching.
- Consider adding a fuzz test that generates random paths with duplicate points and verifies the invariant `output.length <= input.length` holds — this would catch edge cases the current 4 regression tests might miss.
- The test file name `removeDuplicateConsecutivePoints.test.ts` is very long. Consider shortening to `dedupePath.test.ts` but this is cosmetic.

### Confidence Score

**Score:** High

The fix is surgical, the root cause is well-documented, tests cover the key cases (horizontal duplicates, vertical duplicates, empty input, single point), and the snapshot updates confirm the fix resolves real-world rendering issues without regressions.
