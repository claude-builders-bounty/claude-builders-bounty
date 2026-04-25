# claude-review — Claude-powered PR reviewer

A CLI tool that takes a GitHub PR URL, fetches the diff, and uses Claude to generate a structured Markdown code review.

## Output format

```markdown
## 🤖 Claude Code Review — owner/repo#123

## Summary
2-3 sentences describing what the PR does.

## Risks
- Potential issue 1
- Potential regression 2

## Suggestions
- Concrete improvement with file/line reference
- Another suggestion

## Confidence
**Level:** Medium
**Reasoning:** One sentence explanation.
```

## Setup

```bash
pip install anthropic requests
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...   # optional, required for private repos and --post
```

## Usage

```bash
# Print review to stdout
python claude_review.py --pr https://github.com/owner/repo/pull/123

# Write to file
python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md

# Post as PR comment
python claude_review.py --pr https://github.com/owner/repo/pull/123 --post
```

## Sample outputs

See [`sample_output_pr653.md`](sample_output_pr653.md) and [`sample_output_pr655.md`](sample_output_pr655.md) for real reviews generated on PRs in this repo.

## Requirements

- Python 3.9+
- `anthropic` and `requests` packages (`pip install anthropic requests`)
- `ANTHROPIC_API_KEY` environment variable
- `GITHUB_TOKEN` for private repos or posting comments

## How it works

1. Parses the PR URL to extract owner, repo, and PR number
2. Fetches PR metadata (title, description) and diff from GitHub API
3. Truncates diff to ~40k characters if needed (~10k tokens)
4. Sends structured prompt to `claude-sonnet-4-20250514`
5. Outputs Markdown with Summary, Risks, Suggestions, and Confidence sections

## GitHub Action

Add to `.github/workflows/pr-review.yml`:

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
      - name: Install dependencies
        run: pip install anthropic requests
      - name: Run Claude review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python claude_review.py \
            --pr ${{ github.event.pull_request.html_url }} \
            --post
```
