# Claude PR Reviewer

`claude-review` is a small Claude Code-friendly reviewer CLI. It takes a GitHub PR URL, fetches the PR metadata and changed files, and emits a structured Markdown review comment.

## Setup

```bash
export GITHUB_TOKEN=ghp_... # optional, avoids rate limits for public PRs
chmod +x tools/pr-reviewer/claude-review
```

## Usage

```bash
tools/pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123
tools/pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output Shape

Every review includes:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: `Low`, `Medium`, or `High`

The CLI is intentionally dependency-free so it can run in a fresh Claude Code workspace with only Python 3 available.
