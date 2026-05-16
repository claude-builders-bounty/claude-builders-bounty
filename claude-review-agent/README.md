# claude-review: Claude Code PR Review Agent

A CLI tool and GitHub Action that takes a PR URL, fetches the diff via GitHub's GraphQL API, sends it to Claude for analysis, and returns a structured Markdown review.

## Features

- **CLI usage**: `claude-review --pr https://github.com/owner/repo/pull/123`
- **GitHub Action**: automatic PR reviews on PR open/update
- **Structured output**:
  - Summary of changes (2–3 sentences)
  - Identified risks (bullet list)
  - Improvement suggestions (bullet list)
  - Confidence score: Low / Medium / High
- **GitHub GraphQL API**: fetches full diffs, file changes, commit history
- **Tested on real PRs**: sample outputs included in `/samples`

## Setup

### Prerequisites

- Python 3.9+
- GitHub token (`GH_TOKEN` or `GITHUB_TOKEN` env var)
- Anthropic API key (`ANTHROPIC_API_KEY` env var)

### Installation

```bash
pip install anthropic
chmod +x claude-review
# Add to PATH or run directly
./claude-review --pr https://github.com/owner/repo/pull/123
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub PAT or `GITHUB_TOKEN` from GitHub Actions |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude |

## CLI Usage

```bash
# Basic usage
./claude-review --pr https://github.com/owner/repo/pull/123

# Write output to file
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## GitHub Action

Add this workflow to `.github/workflows/pr-review.yml`:

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Claude Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python claude-review-agent/claude-review --pr ${{ github.event.pull_request.html_url }} --output review.md

      - name: Post review comment
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

## Sample Outputs

See `/samples/` directory for example review outputs on real PRs.

## Architecture

1. **GraphQL query**: fetches PR metadata, file changes, diffs
2. **Prompt builder**: formats diff into analysis prompt for Claude
3. **Claude API**: generates structured review
4. **Output**: prints Markdown to stdout or writes to file
