# 🔍 claude-review — PR Review Agent for Claude Code

A **Claude Code sub-agent** that reviews GitHub Pull Requests and generates structured, actionable code reviews.

Part of the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) ($150).

## 🚀 Quick Start

```bash
# Install
pip install claude-review

# Set your GitHub token
export GITHUB_TOKEN=ghp_xxxx

# Review a PR
claude-review --pr https://github.com/owner/repo/pull/123

# Save to file
claude-review --pr https://github.com/owner/repo/pull/123 -o review.md

# View raw diff
claude-review --pr https://github.com/owner/repo/pull/123 --diff-only

# Get JSON output
claude-review --pr https://github.com/owner/repo/pull/123 --json
```

## 📋 Output Structure

The review includes:

- **Overview** — PR title, author, stats
- **Summary of Changes** — Files modified with additions/deletions
- **Identified Risks** — Security concerns, large files, potential issues
- **Improvement Suggestions** — Code quality tips, missing tests, dependencies
- **Confidence Score** — Low / Medium / High based on change size

## 🤖 Using with Claude Code

Add this to your CLAUDE.md or run directly:

```bash
# Claude Code will invoke this sub-agent
claude-review --pr https://github.com/owner/repo/pull/123
```

### As a GitHub Action

Create `.github/workflows/pr-review.yml`:

```yaml
name: PR Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install claude-review
      - run: claude-review --pr "${{ github.event.pull_request.html_url }}" -o review.md
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            await github.rest.issues.createComment({
              ...context.repo,
              issue_number: context.issue.number,
              body: review
            });
```

## 📊 Real PR Examples

Coming from `.examples/` directory after testing.

## 🔧 Requirements

- Python 3.8+
- GitHub Token with `repo` scope (set as `GITHUB_TOKEN` env var)
