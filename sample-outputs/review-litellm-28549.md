# PR Review: Fix/tool call anthropic transformation for vllm
**Repository:** [BerriAI/litellm](https://github.com/BerriAI/litellm)
**PR:** [#28549](https://github.com/BerriAI/litellm/pull/28549)

---

## Summary
This PR fixes a bug in the Anthropic transformation adapter where empty tool_calls arrays were incorrectly treated as valid tool calls, causing text content to be shadowed by empty input_json_delta. The fix changes the condition from checking for null to checking for truthiness, and includes a comprehensive test case.

## Risks
- No significant risks identified. This is a defensive programming fix that handles an edge case more correctly without affecting existing functionality.

## Suggestions
- **Code quality improvement in `transformation.py:1479`**: The change from `if choice.delta.tool_calls is not None:` to `if choice.delta.tool_calls:` is correct and follows Python best practices. This handles both `None` and empty list cases appropriately.
- **Test coverage in new test function**: The test case `test_streaming_chunk_with_text_and_empty_tool_calls_returns_text_delta()` provides excellent coverage for the edge case where providers emit empty `tool_calls: []` arrays. The test validates both the delta transformation and content block transformation paths.
- **Documentation**: The test includes a clear docstring explaining the specific provider behavior this fixes (OpenAI-compatible providers emitting empty tool_calls arrays).

## Confidence
**High**
- The change is simple and focused on a single logical condition
- The fix addresses a clear bug where empty arrays were treated as truthy for tool calls
- Comprehensive test coverage validates the fix works correctly
- The change follows Python idioms and defensive programming practices
- Screenshots show the actual before/after behavior improvement
