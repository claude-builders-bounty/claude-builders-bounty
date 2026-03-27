# Claude Review Agent

AI-powered PR review using GLM (no Anthropic API key required).

## Setup

```bash
pip install requests  # if not installed
export ANTHROPIC_AUTH_TOKEN="your_glm_api_key"
export ANTHROPIC_MODEL="glm-5-turbo"
```

## Usage

```bash
# Review a PR (output to stdout)
python3 claude-review/claude-review.py --pr https://github.com/owner/repo/pull/123

# Save to file
python3 claude-review/claude-review.py --pr https://github.com/owner/repo/pull/123 -o review.md
```

## GitHub Action

Create `.github/workflows/pr-review.yml`:

```yaml
name: AI PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install requests
      - run: python3 claude-review/claude-review.py --pr ${{ github.event.pull_request.html_url }} -o review.md
        env:
          ANTHROPIC_AUTH_TOKEN: ${{ secrets.ANTHROPIC_AUTH_TOKEN }}
          ANTHROPIC_MODEL: glm-5-turbo
      - uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: review
            });
```

## Output Format

```markdown
## Summary
[2-3 sentences]

## Risks
- [risk items]

## Suggestions
- [suggestion items]

## Confidence: Low/Medium/High
[explanation]
```

## Requirements

- Python 3.8+
- `requests` package
- `gh` CLI (authenticated)
- GLM API key (or any Anthropic-compatible API)
