# PR Review: [anthropics/anthropic-sdk-python#756](https://github.com/anthropics/anthropic-sdk-python/pull/756)

## Summary
This PR fixes a regression introduced in v0.26.0 where streaming responses raised an `AttributeError` when the response body contained an unexpected `null` content block. The fix adds a `None` guard in the stream event dispatcher before attempting to access `.type` on the content block object, restoring the prior graceful-skip behaviour.

## Identified Risks
- The guard silently skips `null` content blocks rather than logging or surfacing them; if a `null` block indicates a server-side issue, callers have no way to detect it.
- The fix only covers `MessageStreamEvent` dispatch — if similar `null`-content scenarios exist in the raw SSE parser (`_streaming.py`) they remain unguarded.
- No regression test is added, so the fix could silently break again in a future refactor.

## Improvement Suggestions
- Add a targeted unit test that feeds a `null` content block through the stream dispatcher and asserts no exception is raised.
- Consider emitting a debug-level log line (using the existing `log` logger) when a `null` block is skipped, to aid future diagnostics.
- Update the changelog entry to note the affected version range (v0.26.0–current) so users know whether they need to upgrade.
- Scan `_streaming.py` and `_response.py` for any other `.type` accesses on potentially-null objects while the context is fresh.

## Confidence Score
**High** — The diff is small (< 10 lines), the fix is targeted and easy to reason about, and the root cause is clearly demonstrated by the accompanying reproduction case in the issue thread.
