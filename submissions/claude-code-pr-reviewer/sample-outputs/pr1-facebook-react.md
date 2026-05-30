# PR Review: fix: prevent double invocation of useEffect cleanup

**Repo:** facebook/react  
**PR:** https://github.com/facebook/react/pull/30123

---

## Summary of Changes
This PR fixes a bug where the cleanup function returned by `useEffect` could be invoked twice during strict mode remounts in specific edge cases involving concurrent rendering. The fix adds a guard flag in the fiber's effect list to track whether cleanup has already been executed.

## Identified Risks
- **Regression in Strict Mode**: The guard flag may alter the intentional double-invoke behavior that Strict Mode relies on for detecting side effects
- **Memory leak potential**: If the flag is not reset properly during fiber reuse, cleanup functions in recycled fibers may be skipped entirely
- **Concurrent mode race**: The flag is stored on the fiber which can be mutated during concurrent renders; need to verify atomicity

## Improvement Suggestions
- Consider adding a DEV-only warning when the guard prevents a double invocation, so developers are aware Strict Mode behavior changed
- Add a unit test covering the specific edge case (nested suspense boundaries with useEffect cleanup)
- Document the flag lifecycle in the fiber comment block to aid future maintainers

## Confidence Score
**High**

---

*Reviewed by claude-review v1.0.0*
