# PR Review Agent

This agent reviews a GitHub pull request diff and returns a structured Markdown comment.

## Contract

Input:

- `--pr https://github.com/owner/repo/pull/123`

Output:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

## Review policy

The agent uses the public `.diff` endpoint for a GitHub PR and scans the changed files, line counts, and high-risk terms. It is intentionally deterministic so the same diff produces the same review.

Use it as a first-pass review helper. It does not replace human review for security-sensitive changes.
