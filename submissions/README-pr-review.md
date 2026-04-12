# Claude Code PR Review Agent

An AI-powered PR reviewer that analyzes code changes and returns structured review comments.

## What It Does

- Takes a PR URL or number as input
- Fetches the PR diff automatically
- Analyzes changes using Claude AI
- Returns structured Markdown review with:
  - **Summary** (2-3 sentences)
  - **Identified Risks** (security, performance, bugs)
  - **Improvement Suggestions**
  - **Confidence Score** (High/Medium/Low)
- Posts review directly to GitHub PR as a comment

## Usage

### CLI

```bash
# Review a PR by URL
python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# Review by PR number (must be in repo or specify --repo)
python3 claude-review.py --pr 123 --repo owner/repo --token ghp_xxx

# Post review directly as GitHub comment
python3 claude-review.py --pr 123 --repo owner/repo --post --token ghp_xxx
```

### GitHub Action

Add this to your workflow file:

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Claude Review
        uses: ./.github/workflows/pr-review.yml
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

Or copy `.github/workflows/pr-review.yml` to your repo.

### Sample Output

```
## 🤖 Claude Code PR Review

✅ **Confidence**: High

### Summary
This PR adds user authentication via JWT tokens to the API endpoints. It introduces a new middleware that validates bearer tokens on protected routes and returns 401 for invalid/expired tokens.

## Risks
- JWT secret hardcoded in config — should use environment variable
- No token refresh mechanism — users must re-login after expiration
- Missing rate limiting on auth endpoints — potential brute force vulnerability

## Suggestions
- Move JWT_SECRET to process.env.JWT_SECRET
- Implement token refresh endpoint
- Add rate limiting middleware to /login and /register routes
- Add unit tests for auth middleware edge cases

---
*Reviewed by Claude Code AI — 2026-04-12*
```

## Setup

### 1. Install Dependencies

```bash
pip install anthropic
```

### 2. Set API Key

```bash
export ANTHROPIC_API_KEY=sk-ant-xxxx
```

### 3. (Optional) Set GitHub Token

```bash
export GH_TOKEN=ghp_xxxx
```

### 4. Run

```bash
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
```

## GitHub Action Setup

1. Copy `pr-review.yml` to `.github/workflows/pr-review.yml` in your repo
2. Add `ANTHROPIC_API_KEY` to your repo secrets
3. The action runs automatically on PRs

## Requirements

- Python 3.8+
- `anthropic` package
- `gh` CLI or GitHub token (for posting comments)
- Anthropic API key

## Files

- `claude-review.py` — Main CLI tool
- `pr-review.yml` — GitHub Action
- `README.md` — This file
