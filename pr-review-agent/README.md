# claude-review — PR Review Agent 🦞

A CLI tool and GitHub Action that reviews GitHub Pull Requests and outputs structured Markdown analysis.

```
claude-review --pr https://github.com/owner/repo/pull/123
```

## Features

- **CLI mode** — review any public PR from your terminal
- **GitHub Action** — automatic review on every PR
- **Structured output** — Summary, Risks, Suggestions, Confidence Score
- **AI-powered** — uses free OWL Alpha model via OpenRouter (or bring your own key)
- **Static analysis fallback** — works without any API key
- **Zero dependencies** — pure Python 3 standard library

## Quick Start

```bash
# Review any public PR — no API key needed (uses static analysis)
python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# With AI review (set your OpenRouter key)
OPENROUTER_API_KEY=sk-or-... python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# Save output to file
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md

# Verbose mode
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --verbose
```

## Sample Output

```
# PR Review

**PR:** fix: no lastRec + add tenant_id to unhandled exception
**Author:** shahargl
**Files:** 2 | **+12** / **-3**

## Summary
This PR modifies 2 files with 12 additions and 3 deletions.
Affected types: .py (2 files).

### Files Changed
- `keep/api/alerting.py`: **+7** / **-2**
- `keep/api/exceptions.py`: **+5** / **-1**

## Identified Risks
- No high-risk patterns detected via static analysis.

## Improvement Suggestions
- No test file changes detected — consider adding tests.

## Confidence Score
**High — small, focused change; static analysis passed clean.**
```

See `samples/` for more examples on real PRs.

## GitHub Action

Add `.github/workflows/claude-review.yml` to your repo:

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
      - name: Run claude-review
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        run: |
          curl -sL https://raw.githubusercontent.com/your-org/claude-review/main/claude-review.py -o claude-review.py
          python3 claude-review.py --pr "${{ github.event.pull_request.html_url }}" --output review.md
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

## Bounty

Built for [BOUNTY $150] on the Claude Builders Bounty repo:
https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4

## License

MIT