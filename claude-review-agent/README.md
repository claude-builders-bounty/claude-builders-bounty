# claude-review

CLI agent that reviews a GitHub pull request diff and prints a structured Markdown review comment.

## Setup

```bash
cd claude-review-agent
python3 -m pip install --user .  # optional; script can also run directly
```

For Claude-powered output, install and authenticate Claude Code so `claude -p` works. If Claude is unavailable, the CLI falls back to a deterministic diff-based reviewer.

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

Output includes:
- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

## GitHub Action example

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
      - run: python3 claude-review-agent/claude-review --pr ${{ github.event.pull_request.html_url }} > review.md
      - uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: fs.readFileSync('review.md', 'utf8')
            });
```

## Sample outputs

See `samples/` for reviews generated from real PRs.
