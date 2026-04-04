# claude-review — AI PR Review Agent

A Claude Code sub-agent that reviews GitHub pull requests and outputs structured Markdown reviews.

## Setup

```bash
cp claude-review /usr/local/bin/
chmod +x /usr/local/bin/claude-review
```

Requires: `gh` CLI (authenticated), and either `claude` CLI or `ANTHROPIC_API_KEY` env var.

## Usage

```bash
# Review by URL
claude-review --pr https://github.com/owner/repo/pull/123

# Review by owner/repo#N
claude-review --pr owner/repo#123

# Review by number (uses current repo's remote)
claude-review --pr 123

# Post review as a GitHub comment
claude-review --pr 123 --post

# Save to file
claude-review --pr 123 --output review.md
```

## Output Format

Every review includes:
- **📋 Summary** — 2-3 sentences on what the PR does
- **⚠️ Identified Risks** — security, performance, edge cases, breaking changes
- **💡 Improvement Suggestions** — specific, actionable, with file references
- **🎯 Confidence Score** — Low / Medium / High

## Sample Reviews

- [Sample 1: Changelog Generator PR](./sample-review-1.md)
- [Sample 2: Destructive Command Blocker PR](./sample-review-2.md)

## How It Works

1. Fetches PR metadata and diff via `gh` CLI
2. Constructs a structured prompt with PR context
3. Sends to Claude (via `claude` CLI or direct API)
4. Outputs formatted Markdown review

## GitHub Action

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
      - name: Install gh CLI
        run: sudo apt-get install -y gh
      - name: Run review
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          chmod +x claude-review
          ./claude-review --pr ${{ github.event.pull_request.number }} --post
```
