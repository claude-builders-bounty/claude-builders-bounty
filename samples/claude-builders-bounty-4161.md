# Sample review — public PR #4161

Source: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4161

## Summary

The PR adds a Python CLI that downloads a GitHub pull-request diff and emits a Markdown review with summary, risks, suggestions, and confidence. Its analysis is implemented with deterministic keyword and diff-size heuristics rather than a Claude Code sub-agent.

## Risks

- **High** — `claude-review.py` does not call Claude Code or another semantic model, so the implementation does not meet the stated “Claude Code sub-agent” requirement and can miss correctness issues that are not represented by simple string patterns.
- **Medium** — the diff parser assumes a fixed URL layout and does not visibly validate the pull number before building the API request.
- **Medium** — the PR claims real-PR sample coverage, but the added samples are not visible in this diff, so that acceptance item cannot be verified from the patch.

## Improvement Suggestions

- Invoke `claude -p` (or document a supported model adapter) and keep the deterministic checks as a safety pre-pass.
- Add unit tests for URL parsing, API failures, rate limiting, and the required output headings.
- Commit the two sample outputs and the exact commands or fixtures used to reproduce them.

## Confidence Score

Medium — the complete patch is visible, but the review is limited to the submitted diff and cannot verify external sample files.
