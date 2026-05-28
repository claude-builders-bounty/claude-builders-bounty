# PR Review: expressjs/express#5500

**PR:** [deps: upgrade path-to-regexp to 6.3.0](https://github.com/expressjs/express/pull/5500)
**Author:** @blakeembrey
**Changes:** +12 / -8 across 2 files

---

### Summary

This PR upgrades the `path-to-regexp` dependency from 6.2.2 to 6.3.0, which includes bug fixes for edge cases in route parameter matching. The change also updates the package-lock.json to reflect the new version.

### Risks
- Minor version bump could introduce subtle routing behavior changes for edge-case patterns
- No integration tests were added to verify the specific fixes in 6.3.0

### Suggestions
- Add a test case for the specific edge case fixed in path-to-regexp 6.3.0
- Consider running the full test suite against this upgrade before merging

### Confidence: High
This is a straightforward dependency bump with a minor version change and the upstream changelog shows only bug fixes. Low risk of regression.

---
*Reviewed by claude-review on 2026-05-28*
