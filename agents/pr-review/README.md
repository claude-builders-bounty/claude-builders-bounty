# PR Review Agent — Claude Code Sub-Agent

A Claude Code sub-agent that reviews pull requests and generates structured Markdown review comments.

## Features

- **CLI mode**: `python3 claude-review.py --pr https://github.com/owner/repo/pull/123`
- **GitHub Action**: Auto-review every PR in your repo
- **Structured output**: Summary, file table, risks, suggestions, confidence score
- **Static analysis**: Detects risky patterns (secrets, eval(), destructive commands, etc.)
- **No external deps**: Pure Python 3, stdlib only

## Quick Start

```bash
# Review any public PR
python3 claude-review.py --pr https://github.com/psf/black/pull/4500

# Save output to file
python3 claude-review.py --pr https://github.com/psf/black/pull/4500 -o review.md

# Review from local diff
git diff main...HEAD > /tmp/pr.diff && python3 claude-review.py --diff /tmp/pr.diff

# JSON mode (for programmatic use)
python3 claude-review.py --pr https://github.com/psf/black/pull/4500 --json
```

## GitHub Action Setup

Add this to `.github/workflows/pr-review.yml`:

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
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: python3 agents/pr-review/claude-review.py
          --pr "${{ github.server_url }}/${{ github.repository }}/pull/${{ github.event.pull_request.number }}"
          --output review.md
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const body = fs.readFileSync('review.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body
            });
```

## Output Example

```markdown
## PR Review: Fix crash on empty journal in close command
**Confidence Score:** High

### Summary
This PR handles empty journals in the close command instead of crashing. The change is small and well-targeted.

### Changes by File
| File | + | - | Type |
|------|---|---|------|
| `src/Close.hs` | 5 | 1 | fix |

### Identified Risks
No significant risks detected.

### Improvement Suggestions
No improvement suggestions.
```

## Requirements

- Python 3.10+ (no pip packages needed)
- GitHub API access (public repos work without a token)
- `GITHUB_TOKEN` env var for private repos or higher rate limits

## Claude Code Integration

Load this agent in Claude Code:

```bash
claude --agent agents/pr-review/AGENTS.md
```
