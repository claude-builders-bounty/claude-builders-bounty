name: claude-pr-review
description: >-
  Claude Code sub-agent that reviews a PR and posts a structured comment.
  CLI tool + GitHub Action, outputs structured Markdown review with
  summary, risks, suggestions, and confidence score.
---

# Claude PR Review Agent

A **Claude Code sub-agent** that reviews GitHub PRs and outputs structured Markdown review comments.

## Quick Start

```bash
# Install
pip install requests

# Set your API keys
export GITHUB_TOKEN="ghp_your_token"
export ANTHROPIC_API_KEY="sk-ant_your_key"

# Review a PR
python claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Output Format

```markdown
## 📋 Summary
2-3 sentences summarizing changes.

## ⚠️ Identified Risks
- Risk 1
- Risk 2

## 💡 Improvement Suggestions
- Suggestion 1
- Suggestion 2

## ✅ Confidence Score
**High / Medium / Low**
```

## Features
- CLI mode and GitHub Action mode
- Fetches PR diff + metadata via GitHub API
- Analyzes with Claude API (or local fallback)
- Structured, readable output

## Requirements
- Python 3.8+
- `requests` library
- GitHub Token
- Anthropic API Key (optional — works in local mode without it)
