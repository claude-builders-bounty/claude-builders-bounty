# claude-review — PR Review CLI Agent

> A Claude Code sub-agent that reviews GitHub PRs and produces structured review comments.

## Quick Start

```bash
# Install
npm install -g .   # from this directory

# Or run directly
npx claude-review --pr https://github.com/owner/repo/pull/123

# With output file
npx claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Requires `GITHUB_TOKEN` environment variable (classic PAT or fine-grained token with `public_repo` / `pull_requests:read` scope).

## Output

Generates a structured Markdown review with four sections:

| Section | Description |
|---------|-------------|
| **Summary** | PR title, author, branch, file/line stats, description excerpt |
| **Identified Risks** | Patterns flagged: DB schema changes, config changes, security concerns, large diffs, heavy deletions |
| **Improvement Suggestions** | Error handling, console.log removal, TODO tracking, test gaps, comment ratios |
| **Confidence Score** | Low / Medium / High based on PR size, test coverage, description quality, risk flags |

## Tested Outputs

### Test 1: CLAUDE.md PR (documentation, +242/-47)
```
URL: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2992
Result: Medium confidence — risks flagged for .env references in doc
Output: /tmp/test-review.md
```

### Test 2: npm CLI fix (code, +4/-4)
```
URL: https://github.com/npm/cli/pull/8034
Result: High confidence — small, focused change, no risks
Output: /tmp/test-review2.md
```

## Usage as GitHub Action

```yaml
name: PR Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npx claude-review --pr "${{ github.event.pull_request.html_url }}" --output review.md
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
              body: body
            });
```

## Requirements

- Node.js 18+
- GitHub classic PAT or token with `public_repo` scope (for public PRs)

## How It Works

1. Fetches the PR diff and metadata via the GitHub REST API
2. Analyzes changed files, added/removed lines, and content patterns
3. Scans for risk signals: schema changes, config exposure, security patterns, large diffs
4. Scans for improvement opportunities: missing error handling, console.log, TODOs, test gaps
5. Calculates confidence score based on PR size, structure, and risk indicators
6. Produces structured Markdown output
