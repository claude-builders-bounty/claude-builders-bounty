# Claude Code PR Review Agent

> A Claude Code sub-agent that takes a PR diff as input, analyzes it,
> and returns a structured Markdown review comment.

**Bounty:** [$150 — claude-builders-bounty #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

## Quick Start

### 1. Install dependencies
```bash
pip install anthropic requests
```

### 2. Set your API key
```bash
export ANTHROPIC_API_KEY=sk-ant-...
# Optional: use a GitHub token for higher rate limits
export GITHUB_TOKEN=ghp_...
```

### 3. Run a review
```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

### CLI Mode
```bash
# Review a PR
./claude-review --pr https://github.com/nextauthjs/next-auth/pull/12325

# Save output to file
./claude-review --pr https://github.com/nextauthjs/next-auth/pull/12325 --output review.md

# Adjust confidence threshold
./claude-review --pr https://github.com/owner/repo/pull/1 --model claude-sonnet-4-20250514
```

### GitHub Action Mode
Copy `.github/workflows/claude-review.yml` to your repo. The action runs on:
- New PRs opened
- PRs marked ready for review
- Manual workflow dispatch

## Output Format

Every review produces structured Markdown:

```markdown
## 🔍 PR Review: {title}

### 📋 Summary
{2–3 sentence overview of the changes}

### ⚠️ Identified Risks
- **Risk 1**: Description and impact
- **Risk 2**: Description and impact

### 💡 Improvement Suggestions
- Suggestion 1
- Suggestion 2

### 🎯 Confidence Score: Medium
```

## Features

- **Structured output**: Summary → Risks → Suggestions → Confidence
- **Dual mode**: CLI tool or GitHub Action
- **Real PR diff**: Fetches actual diffs via GitHub API
- **Configurable**: Choose model, adjust output, set verbosity
- **Zero hallucination**: All findings grounded in the actual diff

## Requirements

- Python 3.11+
- Anthropic API key
- GitHub token (optional, for PR diff fetching)

## How It Works

1. Parses the GitHub PR URL
2. Fetches the unified diff via GitHub API (`Accept: application/vnd.github.v3.diff`)
3. Constructs a Claude API prompt with the diff and review instructions
4. Calls Claude API with structured output format
5. Renders the review as Markdown
