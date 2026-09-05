# Claude Code PR Review Sub-Agent

A lightweight, autonomous sub-agent designed to review GitHub Pull Request diffs and output structured, actionable Markdown feedback.

## Features
- **CLI Tool:** Direct terminal execution via `--pr <url>`.
- **GitHub Action Workflow:** Reusable CI integration.
- **Structured Markdown Output:**
  - Executive Summary of changes.
  - Identified Security/Code Risks.
  - Actionable Improvement Suggestions.
  - Confidence Score (`High`, `Medium`, `Low`).

## Installation & Usage

```bash
# Direct run
python3 claude_review.py --pr https://github.com/owner/repo/pull/123

# Save output to file
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

## GitHub Action Workflow (`.github/workflows/pr-review.yml`)

```yaml
name: Claude PR Review Agent

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run Review Agent
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 claude_review.py --pr ${{ github.event.pull_request.html_url }} --output review.md

      - name: Comment Review on PR
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: review
            });
```
