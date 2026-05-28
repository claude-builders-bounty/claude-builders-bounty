# Claude Code PR Review Agent

> Bounty #4 — $150 — [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

A Claude Code sub-agent that takes a GitHub pull request URL, fetches the diff, analyzes it via DeepSeek API, and returns a structured Markdown review.

## Quick Start

```bash
# 1. Set API keys
export DEEPSEEK_API_KEY=sk-...
export GITHUB_TOKEN=ghp_...

# 2. Review a PR
python claude-review --pr https://github.com/owner/repo/pull/123

# 3. Save to file
python claude-review --pr <url> --output review.md

# 4. Post review as PR comment
python claude-review --pr <url> --post
```

## Output Format

- **Summary**: 2-3 sentences of what changed and why
- **Identified Risks**: Specific risks with file references
- **Improvement Suggestions**: Actionable, concrete suggestions
- **Confidence Score**: High / Medium / Low with explanation

## GitHub Action

Copy `review-pr.yml` to `.github/workflows/` and set repository secrets:
- `GITHUB_TOKEN` (auto-provided by GitHub Actions)
- `DEEPSEEK_API_KEY`

## Requirements

- Python 3.10+
- `httpx` (pip install httpx)
- DeepSeek API key
- GitHub personal access token with `public_repo` scope
