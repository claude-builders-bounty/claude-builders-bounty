## PR Review

> **PR**: openai/openai-node#1867
> **Title**: Update README models to gpt-5.5 and gpt-realtime-2
> **Author**: @romainhuet

### Summary
This PR is a documentation-only refresh that updates README examples from `gpt-5.2` to `gpt-5.5` and from `gpt-realtime` to `gpt-realtime-2`. It also updates the Realtime event listener examples from `response.text.delta` to `response.output_text.delta`, so the main effect is aligning the public examples with newer model and event names.

### Identified Risks
- The README examples assume that every referenced API surface already supports `gpt-5.5` and `gpt-realtime-2`; if any SDK behavior or server-side naming is not fully rolled out, the docs will become ahead of the product.
- The Realtime event rename is more than a cosmetic change. If any surrounding docs, tests, or migration notes still mention `response.text.delta`, users may copy mixed examples and end up with broken listeners.
- This PR changes many repeated snippets in one file. Repetition-heavy edits are easy to merge, but they also make it easy to miss one stale model name elsewhere in the docs set.

### Improvement Suggestions
- Add a short note in the README or changelog clarifying whether `gpt-5.5` replaces `gpt-5.2` as the recommended default, or whether this is only a docs modernization pass.
- Verify that all Realtime documentation consistently uses `response.output_text.delta`, especially in any linked files such as `realtime.md`, so users do not see two event names for the same pattern.
- Run a docs-wide search for `gpt-5.2`, `gpt-4`, and `gpt-realtime` to confirm there are no remaining stale examples outside `README.md`.

### Confidence
High
