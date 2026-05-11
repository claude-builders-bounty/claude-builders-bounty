# PR Review Agent

`claude-review` fetches a GitHub pull request diff and prints a structured Markdown review comment.

## Setup

```bash
chmod +x pr-review-agent/claude-review
```

To make it available as `claude-review` from anywhere:

```bash
ln -sf "$PWD/pr-review-agent/claude-review" /usr/local/bin/claude-review
```

## Usage

```bash
pr-review-agent/claude-review --pr https://github.com/owner/repo/pull/123
```

Optional:

```bash
GITHUB_TOKEN=ghp_xxx pr-review-agent/claude-review --pr https://github.com/owner/repo/pull/123
```

## Output Format

The review includes:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score

The CLI is deterministic and works without an API key. When `GITHUB_TOKEN` is set it uses authenticated GitHub API requests for higher rate limits.

## GitHub Action

Copy `pr-review-agent/github-action/pr-review.yml` to `.github/workflows/pr-review.yml` to post the structured review automatically on pull requests.

## Sub-Agent Prompt

`pr-review-agent/agent.md` contains the review-agent behavior and required Markdown format.

## Test

```bash
python3 pr-review-agent/test_claude_review.py
```
