# Claude PR Review Agent

`claude-review` is a small CLI agent that fetches a GitHub PR diff and returns a structured Markdown review comment.

It can also post the review back to the PR when `GITHUB_TOKEN` is available.

## Setup

```bash
chmod +x claude-review
export PATH="$PWD:$PATH"
```

## Usage

Print a review:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Write a review to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Post a review comment:

```bash
GITHUB_TOKEN=ghp_your_token claude-review --pr https://github.com/owner/repo/pull/123 --post
```

The token needs permission to read the PR and create issue comments.

## Output Format

The generated Markdown includes:

- Summary of changes
- Files reviewed
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

## Review Heuristics

The agent scans the diff for:

- large changes
- database migrations or schema files
- GitHub Actions workflow changes
- secret-handling code
- dynamic execution or HTML injection patterns
- destructive operations
- missing test changes

This is a deterministic first-pass reviewer. It is meant to catch review focus areas quickly, not replace project-specific human judgment.

