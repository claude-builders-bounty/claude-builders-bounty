## Summary of Changes

This PR adds streaming support for the Messages API beta features, including
token-level streaming for tool use blocks. It modifies the core streaming
handler to properly accumulate and yield tool input chunks.

## Identified Risks

- **Partial tool input on error**: If the stream is interrupted mid-tool-input,
  the accumulated partial JSON is silently discarded. Callers have no way to
  detect this happened.
- **Breaking change in Stream.handle_event()**: The method signature changed
  from returning `None` to returning an `Event`. Code calling the old signature
  will get unexpected return values.

## Improvement Suggestions

- Add a `Stream.on_tool_input_error` callback so callers can handle partial
  tool input gracefully.
- Document the breaking change in `handle_event()` in the PR description and
  consider a deprecation path.
- Add tests for the stream-interruption-during-tool-input edge case.

## Confidence Score

**Medium** — The streaming logic is correct but the breaking change and
error handling gaps need attention before merge.
