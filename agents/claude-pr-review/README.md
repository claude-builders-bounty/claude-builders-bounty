# Claude PR Review Agent

Zero-dependency CLI agent that fetches a GitHub pull request diff and prints a
structured Markdown review comment.

## Setup

```bash
python3 agents/claude-pr-review/claude_review.py --pr https://github.com/owner/repo/pull/123
```

For private repositories or higher API limits, set `GITHUB_TOKEN` before
running the command.

## Output

The review always includes:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

This agent intentionally uses deterministic heuristics instead of a paid API, so
it can run in local Claude Code workflows and GitHub Actions without additional
secrets.

## GitHub Action

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
      - name: Generate structured PR review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 agents/claude-pr-review/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            > claude-pr-review.md
          cat claude-pr-review.md
```

## Sample Runs

- [sample-code-server-1309.md](samples/sample-code-server-1309.md)
- [sample-waymark-1.md](samples/sample-waymark-1.md)
