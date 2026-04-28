# Claude PR Review Agent

A CLI tool that reviews GitHub pull requests using Claude API and posts structured Markdown comments.

**Bounty:** $150 — powered by [Opire](https://opire.dev)

## Quick Start

```bash
# 1. Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# 2. Review a PR
python3 claude-review/pr-review.py --pr https://github.com/owner/repo/pull/123
```

## Output Format

```
## Summary
(2-3 sentence summary of changes)

### Identified Risks
- Risk 1

### Improvement Suggestions
1. Suggestion 1

### Confidence Score
**High** / Medium / Low
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--pr` | Full GitHub PR URL (required) |
| `-o, --output` | Save to file |
| `--custom-instructions` | Extra context for review |
| `--github-token` | GitHub token (defaults to GITHUB_TOKEN env) |

## Requirements

- Python 3.8+
- `ANTHROPIC_API_KEY` environment variable

## Sample Outputs

### PR #5 (n8n weekly workflow, +6,350/-14)

## Summary
Adds a complete n8n weekly dev summary workflow that fetches GitHub activity and generates a narrative report via Claude API. The workflow includes cron scheduling (Friday 5pm), GitHub API pagination, multi-language support (EN/FR), and Slack webhook delivery.

### Identified Risks
- **Missing screenshot** — No execution screenshot is included; maintainer will need to deploy and verify manually
- **Claude API key exposure** — The workflow reads ANTHROPIC_API_KEY from env; if n8n credentials are shared, the key could leak
- **No error handling for API failures** — If Claude API is down, the workflow fails without retry or fallback

### Improvement Suggestions
1. Add a retry node for Claude API calls (n8n supports Error Trigger)
2. Add optional email fallback if Slack webhook fails
3. Add a .env.example for the config variables

### Confidence Score
**Medium** — Well-structured workflow but lacks error handling and verification screenshot

### PR #1 (CHANGELOG skill, +183/-1)

## Summary
Adds a comprehensive CHANGELOG generator as a bash script. It fetches commits since the last git tag, categorizes them into Added/Fixed/Changed/Removed, and outputs formatted CHANGELOG.md.

### Identified Risks
- **No test suite** — The generated CHANGELOG output is not validated; malformed git history could produce broken output
- **Tag assumption** — If there are no git tags in the repo, the script errors with `fatal: No names found`
- **Commit convention dependency** — Relies on conventional commit format; unstructured messages get "Other" category

### Improvement Suggestions
1. Add a fallback when no git tags exist (use --since with a date range)
2. Add --dry-run flag to preview output without writing to file
3. Add support for custom commit category mappings

### Confidence Score
**High** — Clean implementation with good output formatting, tested against real PRs

## GitHub Action Setup

To auto-review every PR:
1. Add `ANTHROPIC_API_KEY` as a repository secret
2. Copy this workflow to `.github/workflows/pr-review.yml`:

```yaml
name: PR Review Agent
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Review PR
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python3 claude-review/pr-review.py --pr "${{ github.event.pull_request.html_url }}" --output review.md
      - name: Post Comment
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
