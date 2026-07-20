# Claude PR Reviewer Agent

An autonomous Claude Code sub-agent packaged as a GitHub Action. It takes a PR diff as input, analyzes it using Anthropic's Claude 3.7 Sonnet, and returns a structured Markdown review comment directly on the PR.

## Features
- **Summary of Changes**: Provides a quick 2-3 sentence summary of the PR.
- **Identified Risks**: Highlights security, logic, or performance risks.
- **Improvement Suggestions**: Suggests clean code refactors and optimizations.
- **Confidence Score**: Scores the review (Low / Medium / High) with an explanation.

## Usage

Add this to your repository in `.github/workflows/claude-review.yml`:

```yaml
name: Claude PR Reviewer

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Run Claude PR Review
        uses: claude-builders-bounty/claude-builders-bounty/actions/claude-pr-reviewer@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Setup
1. Go to your repository **Settings > Secrets and variables > Actions**.
2. Add a new repository secret named `ANTHROPIC_API_KEY` with your Anthropic API key.
3. Ensure GitHub Actions has permission to write comments (`permissions: pull-requests: write`).
