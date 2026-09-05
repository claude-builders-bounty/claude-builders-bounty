# Claude PR Review Agent

A Claude Code sub-agent that reviews GitHub PRs and posts structured Markdown review comments.

## Features

- Fetches PR metadata, diff, and file changes from GitHub API
- Generates structured review with:
  - Summary of changes (2-3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score (Low / Medium / High)
- Posts review as a PR comment
- Supports dry-run mode for testing

## Setup

### Prerequisites

- Python 3.8+
- GitHub token (via `GITHUB_TOKEN` env var or `gh auth login`)

### Installation

```bash
# No installation needed — single file script
# Just ensure Python 3.8+ is available
```

## Usage

### CLI Usage

```bash
# Review a PR and post comment
python claude-review.py https://github.com/owner/repo/pull/123

# Dry run (print review without posting)
python claude-review.py https://github.com/owner/repo/pull/123 --dry-run

# Save review to file
python claude-review.py https://github.com/owner/repo/pull/123 --output review.md
```

### GitHub Action

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
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run PR Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python agents/pr-reviewer/claude-review.py \
            https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }}
```

## Output Format

```markdown
## 🤖 AI Code Review

### Summary
PR by @author: Title. Changes X files with +Y/-Z lines. Description...

### Identified Risks
- ⚠️ Large PR with 500+ additions
- ⚠️ No test files modified

### Improvement Suggestions
- 💡 Consider breaking this PR into smaller PRs
- 💡 Add unit tests

### Confidence Score: **Medium**

---
*Files: 5 | +200/-50*
```

## Testing

Test on real PRs:

```bash
# Test on a small PR
python claude-review.py https://github.com/octocat/Hello-World/pull/1 --dry-run

# Test on a larger PR
python claude-review.py https://github.com/facebook/react/pull/27000 --dry-run
```

## How It Works

1. Parses the PR URL to extract owner/repo/number
2. Fetches PR metadata, diff, and file list from GitHub API
3. Analyzes the changes:
   - Counts additions/deletions
   - Checks for test coverage
   - Identifies risk patterns (large PRs, security files, env files)
   - Generates improvement suggestions
4. Formats the review as structured Markdown
5. Posts the comment on the PR (or prints in dry-run mode)

## License

MIT
