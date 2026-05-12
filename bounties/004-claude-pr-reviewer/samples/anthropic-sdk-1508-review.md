# Sample Review — anthropics/anthropic-sdk-python#1508

**Command used:**
```
claude-review --pr https://github.com/anthropics/anthropic-sdk-python/pull/1508
```

**PR metadata:** "Add structured output guidance"
Author: RobertCraigie · Files changed: 3 · +41/-0

---

## Summary

This PR adds a `## Structured outputs` section to the SDK README documenting `client.messages.parse()` with `output_format=`, and adds two brief inline comments to the existing structured output examples clarifying why `messages.parse()` avoids the tool-use transcript pattern. No existing behavior is modified — it is purely additive documentation.

## Identified Risks

- **Example model pinned to `claude-sonnet-4-5`**: The README example hard-codes a model string that will become outdated as newer versions ship. Users copy-paste examples verbatim; consider using a `claude-3-5-sonnet-latest` alias or noting that any current model works.
- **`parsed_output` attribute undocumented**: The example calls `print(parsed_message.parsed_output)` but neither the README nor the diff shows the return type. First-time readers may not know whether `parsed_output` is the Pydantic model instance or a dict.
- No behavioral risks — the change is docs-only with no code path modifications.

## Improvement Suggestions

- Replace `"claude-sonnet-4-5"` with a stable alias (`"claude-3-5-sonnet-latest"`) or add a comment: `# or any model that supports structured output`.
- Add a one-line note on `parsed_message.parsed_output` type: `# → Order(product_name='Green Tea', price=5.5, quantity=2)` as a docstring comment.
- The two example file comments are helpful; consider whether the streaming example comment could also mention that `output_format` works identically to the non-streaming path to avoid reader confusion.

## Confidence Score

**High** — 41 additions across 3 files, all documentation. No logic changes, no test risk. The suggestions are minor polish, not correctness issues.
