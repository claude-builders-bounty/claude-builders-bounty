# claude-review: AI-Powered PR Review Agent

A Claude Code sub-agent that takes a PR diff as input, analyzes it, and returns a structured Markdown review comment.

## Features

- Fetches PR diffs directly from GitHub
- Analyzes code changes using Claude (CLI or API)
- Outputs structured Markdown with: Summary, Risks, Suggestions, Confidence Score
- Can post reviews as PR comments automatically
- Includes GitHub Action workflow for automatic reviews on every PR
- Falls back to static analysis if Claude is unavailable

## Setup

### Option 1: CLI Usage

```bash
# Install
cp agents/claude-review/claude-review.py /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review

# Set environment variables
export GITHUB_TOKEN="ghp_your_token_here"
export ANTHROPIC_API_KEY="sk-ant-your_key_here"  # Optional, falls back to claude CLI

# Review a PR
claude-review --pr https://github.com/owner/repo/pull/123

# Review and post as comment
claude-review --pr https://github.com/owner/repo/pull/123 --post

# Review a local diff file
claude-review --diff-file changes.diff

# JSON output
claude-review --pr https://github.com/owner/repo/pull/123 --output json
```

### Option 2: GitHub Action

1. Copy `agents/claude-review/github-action.yml` to `.github/workflows/claude-review.yml`
2. Add `ANTHROPIC_API_KEY` as a repository secret
3. Every PR will automatically get a review comment

```yaml
# .github/workflows/claude-review.yml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize, reopened]
jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python3 agents/claude-review/claude-review.py \
            --pr "${{ github.event.pull_request.html_url }}" --post
```

## Output Format

```markdown
## Summary

[2-3 sentences summarizing what this PR changes]

## Identified Risks

- [Risk 1]
- [Risk 2]

## Improvement Suggestions

- [Suggestion 1]
- [Suggestion 2]

## Confidence Score

**[Low / Medium / High]** — [1 sentence explaining the confidence level]
```

## Sample Outputs

See `sample-output-1.md` and `sample-output-2.md` for real review outputs tested on actual GitHub PRs.

## How It Works

1. Fetches PR metadata and diff via GitHub API
2. Sends diff to Claude for analysis (tries CLI first, then API, then static fallback)
3. Claude analyzes the diff for risks, improvements, and overall quality
4. Outputs structured Markdown review
5. Optionally posts as a comment on the PR

## Requirements

- Python 3.10+
- `GITHUB_TOKEN` environment variable (for fetching PRs and posting comments)
- One of:
  - `claude` CLI installed and in PATH
  - `ANTHROPIC_API_KEY` environment variable
  - Neither (uses static analysis fallback with reduced accuracy)
