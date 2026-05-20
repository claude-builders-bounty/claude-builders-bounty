# Claude PR Review Agent

`claude-review` is a lightweight CLI that fetches a GitHub PR diff and prints a structured Markdown review comment suitable for Claude Code workflows.

## Setup

```bash
chmod +x pr-review-agent/claude-review
export GITHUB_TOKEN=ghp_xxx   # optional, recommended for private repos/rate limits
```

## Usage

```bash
pr-review-agent/claude-review --pr https://github.com/owner/repo/pull/123
```

The output contains:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

## Notes

The CLI is deterministic and does not require an LLM API key. In a Claude Code setup, pipe its Markdown into Claude or post it as a PR comment after human/agent review.
