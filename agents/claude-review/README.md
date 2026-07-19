# Claude Code PR Reviewer Sub-Agent

An automated, risk-aware Pull Request review sub-agent designed for Claude Code and GitHub Actions. Analyzes PR diffs and metadata, produces structured Markdown reviews, identifies security/quality risks, and assigns a confidence score.

## Features

- **CLI & CI/CD Support**: Runs standalone via terminal or automatically inside GitHub Actions workflows.
- **Structured Markdown Output**:
  - **Summary of Changes**: Concise 2–3 sentence overview of modifications.
  - **Identified Risks**: Security checks (hardcoded secrets, unvalidated inputs, swallowed exceptions, SQL safety, missing tests).
  - **Improvement Suggestions**: Actionable recommendations for refactoring, test coverage, and code quality.
  - **Confidence Score**: Low / Medium / High rating with underlying rationale.
- **Zero Heavy Dependencies**: Built using standard Python standard libraries + GitHub REST API.

## Installation & Setup

```bash
cd agents/claude-review
chmod +x pr_reviewer.py
```

## CLI Usage Examples

### 1. Review via PR URL
```bash
python pr_reviewer.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3515
```

### 2. Save Markdown Output to File
```bash
python pr_reviewer.py --pr https://github.com/owner/repo/pull/123 --output samples/review.md
```

---

## GitHub Action Workflow Integration

Create `.github/workflows/pr-reviewer.yml` in your repository:

```yaml
name: Claude PR Reviewer

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
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run PR Reviewer Sub-Agent
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python agents/claude-review/pr_reviewer.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --output pr_review.md

      - name: Comment PR Review
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const body = fs.readFileSync('pr_review.md', 'utf8');
            await github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```
