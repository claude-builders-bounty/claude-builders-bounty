## Summary
This PR adds a focused PR-review agent CLI that fetches a GitHub PR diff and produces a structured review. The implementation keeps a deterministic fallback while preferring Claude Code when available.

## Risks
- Verify subprocess failures remain explicit and do not silently mask GitHub authentication or network errors.
- Keep generated review output bounded to the supplied diff.

## Improvement suggestions
- Preserve the existing output-contract tests and add a real-binary verification receipt.
- Document the verification boundary when a local Anthropic-compatible endpoint is used.

## Confidence
High
