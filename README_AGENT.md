# Claude Review Agent

A CLI tool and GitHub Action that analyzes PR diffs and produces structured Markdown reviews.

## Features

- **CLI mode**: `claude-review --pr <URL>` — analyze any GitHub PR from your terminal
- **GitHub Action mode**: Auto-review PRs when they're opened/updated
- **Structured output**: Summary, Risks, Suggestions, Confidence Score
- **LLM-powered**: Uses any OpenAI-compatible API (OpenAI, Anthropic via proxy, local models)
- **Fallback**: Works without LLM using heuristic analysis

## Quick Start

### CLI Usage

```bash
# Set environment variables
export GITHUB_TOKEN="ghp_..."        # or use `gh auth login`
export OPENAI_API_KEY="sk-..."       # optional, enables LLM analysis
export OPENAI_BASE_URL="https://api.openai.com/v1"  # optional

# Review a PR
python claude_review.py --pr https://github.com/owner/repo/pull/123

# Output to file
python claude_review.py --pr https://github.com/owner/repo/pull/123 -o review.md

# JSON output
python claude_review.py --pr https://github.com/owner/repo/pull/123 --json
```

### GitHub Action

Add this workflow to your repo at `.github/workflows/claude-review.yml`:

```yaml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  pull-requests: write
  contents: read

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Run Claude Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: python claude_review.py --pr "${{ github.event.pull_request.html_url }}" -o review.md
      - name: Post Review Comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            const prNumber = context.payload.pull_request.number;
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: prNumber,
              body: review,
            });
```

## Output Format

```markdown
## 🔍 PR Review

**PR:** https://github.com/owner/repo/pull/123
**Author:** @username
**Changes:** 5 files, +120/-30

### 📝 Summary
This PR adds user authentication with JWT tokens and updates the login flow.

### ⚠️ Risks
- Password handling may need review for security
- Large changeset across multiple modules

### 💡 Suggestions
- Add unit tests for the auth middleware
- Consider rate limiting on login endpoint

### 🎯 Confidence: 🟡 Medium
```

## Requirements

- Python 3.9+
- `GITHUB_TOKEN` (or authenticated `gh` CLI)
- `OPENAI_API_KEY` (optional — falls back to heuristic analysis)

## License

MIT
