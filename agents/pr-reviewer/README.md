# claude-review — PR Review Agent

A Claude Code sub-agent that reviews GitHub PRs and posts structured feedback.

## Setup

1. Set `GITHUB_TOKEN` in your environment (GitHub personal access token)
2. Run: `python claude-review.py --pr https://github.com/owner/repo/pull/123`

## GitHub Action

Copy `.github/workflows/pr-review.yml` into your repo to auto-review every PR.

## Output

- Summary of changes
- Identified risks (high/medium/low severity)
- Improvement suggestions
- Confidence score (Low / Medium / High)

## Example

```bash
GITHUB_TOKEN=ghp_xxx python claude-review.py --pr https://github.com/numpy/numpy/pull/31848
```

See [`samples/`](samples/) for real PR outputs.
