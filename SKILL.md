# PR Review Agent

A Claude Code skill that reviews GitHub PRs and posts structured feedback.

## Usage

```
claude-review --pr https://github.com/owner/repo/pull/123
```

Or as a Claude Code command: `/review-pr https://github.com/owner/repo/pull/123`

## Output

Structured Markdown with:
- Summary of changes (2-3 sentences)
- Identified risks (list)
- Improvement suggestions (list)
- Confidence score: Low / Medium / High
