## Summary
This PR replaces the deprecated `pytest-freezegun` package with `time-machine` across the test suite. The change modernizes the test infrastructure by swapping out a frozen-time library that is no longer maintained for a more performant and actively maintained alternative. The diff is small and focused, touching 6 files with minimal line changes.

## Identified Risks
- **API compatibility**: `time-machine` has a slightly different API from `freezegun` — the `travel()` context manager behaves differently from `freeze_time()`. The tests may pass locally but could behave unexpectedly with more complex time-dependent code.
- **Missing coverage**: If any test indirectly relied on `freezegun` features like `start()`/`stop()` that aren't directly replicated, those scenarios aren't covered.

## Improvement Suggestions
- Consider adding a short CI job that explicitly verifies `time-machine` works correctly with the project's time-sensitive test patterns.
- Pin the `time-machine` major version in dependencies to avoid unexpected breaking changes.

## Confidence Score
**Confidence: High**

The changes are mechanical and well-scoped — a straightforward library swap with clear 1:1 replacement patterns.
