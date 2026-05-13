# PR Review: Fix useEffect cleanup race condition in Suspense boundaries

> **PR:** [#28543](https://github.com/facebook/react/pull/28543) | **Author:** sebmarkbage | **Changes:** +87/-23 in 4 files
> **Reviewed by:** Claude Code PR Review Agent v1.0.0
> **Date:** 2026-05-13T14:22:00Z

---

### Summary

This PR fixes a race condition in `useEffect` cleanup functions when a component is suspended inside a Suspense boundary. The fix ensures that cleanup functions are invoked in the correct order by tracking the fiber's commit phase state before scheduling the passive effect destruction. The change touches the reconciler's commit phase logic and adds a regression test covering the specific scenario where a cleanup function references stale state during concurrent rendering.

### Identified Risks

- **Concurrency edge case:** The new ordering guarantee relies on the `pendingPassiveEffectsLanes` check happening before the `commitPassiveUnmountOnFiber` call. If future refactors reorder these operations, the race condition could reappear without test coverage catching it immediately.
- **Performance consideration:** The additional lane check in the hot path of `commitPassiveUnmountEffects` adds a branch prediction point. In benchmarks this should be negligible, but it is worth verifying with the React profiler on large trees.
- **Backward compatibility:** Components that accidentally depended on the previous (incorrect) cleanup ordering may observe different behavior. This is technically a bug fix, but could surface issues in user-land code that worked around the bug.
- **Missing coverage for nested Suspense:** The test covers a single Suspense boundary, but the fix should also be validated against nested `<Suspense>` trees with independent fallbacks to confirm correctness.

### Improvement Suggestions

- Add a test case with nested Suspense boundaries (`<Suspense><Suspense>...</Suspense></Suspense>`) to verify cleanup ordering propagates correctly through multiple suspension points.
- Consider adding an `__DEV__`-only warning when a cleanup function is called after the component has already been removed from the tree, which would help developers catch related issues earlier.
- The inline comment in `ReactFiberCommitWork.js` at line 2847 explains the "why" well, but referencing the GitHub issue number (e.g., `// See #28401`) would help future maintainers trace the history.
- The test file `ReactSuspenseEffectsSemantics-test.js` is growing large (1200+ lines). Consider splitting Suspense effect tests into focused suites (mount/unmount/update) for better maintainability.

### Confidence Score

**Medium** -- The diff is focused and the fix is logically sound, but without full visibility into the React reconciler's internal scheduling and the broader test suite, there is some uncertainty about whether the lane check covers all concurrent rendering scenarios. The change is in a critical code path, so thorough integration testing is advisable.
