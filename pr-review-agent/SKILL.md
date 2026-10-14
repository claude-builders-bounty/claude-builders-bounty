---
name: pr-review-agent
description: Use when reviewing a GitHub pull request with an LLM — fetches the PR diff and produces a structured Markdown review (Summary, Risks, Suggestions, Confidence), optionally posting it as a PR comment.
---

# PR Review Agent

Run `claude-review` against any GitHub PR to get a structured review.

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123           # stdout
claude-review --pr https://github.com/owner/repo/pull/123 --post    # comment on the PR
```

Requires `LLM_BASE_URL` (any OpenAI-compatible endpoint), `LLM_MODEL`, and
`LLM_API_KEY` unless the local router substitutes its own key. `GITHUB_TOKEN`
is optional but recommended (rate limits, private repos, `--post` fallback).

## Output contract

The review must contain `## Summary`, `## Risks`, `## Suggestions`, and a
`**Confidence:**` line. The CLI validates all four and exits non-zero when
any is missing — a missing section means the model misbehaved, not that the
PR is clean.

## Verify

Re-run against a PR you know and check the summary names the actual files
changed. If the diff was truncated (> `MAX_DIFF_CHARS`), the prompt says so
and confidence should reflect it.
