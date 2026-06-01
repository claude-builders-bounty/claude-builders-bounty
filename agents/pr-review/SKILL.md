---
name: pr-review
description: Review a GitHub pull request and return structured feedback. Use /review-pr or claude-review --pr URL.
---

# PR Review Agent

Analyzes a GitHub pull request diff and returns a structured Markdown review.

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

## Output Format

The agent returns a structured review with:
- Summary of changes (2–3 sentences)
- Identified risks (bulleted list)
- Improvement suggestions (bulleted list)
- Confidence score: Low / Medium / High

## How It Works

1. Fetches PR diff via `gh pr diff`
2. Analyzes the changeset size, patterns, and potential issues
3. Generates a structured report
4. Posts as a comment (optional: `--post`)
