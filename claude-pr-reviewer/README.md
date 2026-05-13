# Claude PR Reviewer

`claude-review` reviews a GitHub pull request diff and prints a structured Markdown review comment.

It prefers Claude Code when the `claude` CLI is installed. For CI, demos, or environments without Claude Code, `--no-claude` uses a deterministic local reviewer that still produces the required Markdown structure.

## Setup

```bash
chmod +x claude-pr-reviewer/claude-review
cp claude-pr-reviewer/claude-review /usr/local/bin/claude-review
```

If you want Claude-powered reviews, install and authenticate Claude Code first:

```bash
npm install -g @anthropic-ai/claude-code
claude auth login
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Output sections:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

For deterministic output without calling Claude Code:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --no-claude
```

## GitHub Action example

```yaml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm install -g @anthropic-ai/claude-code
      - run: cp claude-pr-reviewer/claude-review /usr/local/bin/claude-review && chmod +x /usr/local/bin/claude-review
      - run: claude-review --pr "${{ github.event.pull_request.html_url }}" > review.md
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs')
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: fs.readFileSync('review.md', 'utf8')
            })
```

## Sample outputs

Two real PR review samples are included:

- `samples/projecthunt-pr-4-review.md`
- `samples/claude-builders-pr-1176-review.md`
