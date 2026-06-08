# claude-review — AI PR Review Agent

A Claude Code sub-agent that analyzes PR diffs and produces structured code reviews.

## Quick Start

### Prerequisites
- Python 3.6+

### Usage

Review a PR:
  python3 claude_review.py --pr https://github.com/owner/repo/pull/123

Review a local diff:
  python3 claude_review.py --diff /path/to/changes.diff

Save output to file:
  python3 claude_review.py --pr https://github.com/owner/repo/pull/123 -o review.md

## Output

### Summary of Changes
[2-3 sentence summary]

### Identified Risks
- Risk items...

### Improvement Suggestions
- Suggestions...

---
**Confidence Score:** Medium

## GitHub Action

Add .github/workflows/pr-review.yml to auto-review PRs:

```yaml
name: AI PR Review
on: [pull_request_target]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          curl -sL https://raw.githubusercontent.com/rock2089/claude-review-agent/main/claude_review.py -o review.py
          python3 review.py --pr ${{ github.event.pull_request.html_url }}
```

## Env Variables
- GITHUB_TOKEN - for GitHub API access
- ANTHROPIC_API_KEY - optional AI-powered reviews (falls back to diff analysis)
