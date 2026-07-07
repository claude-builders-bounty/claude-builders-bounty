# Claude Code PR Review Agent

AI-powered PR review agent for Claude Code.

## CLI Usage

```bash
export GITHUB_TOKEN=ghp_xxx
./claude-review.sh --pr https://github.com/owner/repo/pull/123
```

## GitHub Action Usage

```yaml
name: PR Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: feezy1357/pr-review-action@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          pr-number: ${{ github.event.pull_request.number }}
```

## Output Format
- Summary of changes (2-3 sentences)
- Identified risks (severity-categorized)
- Improvement suggestions (actionable)
- Overall assessment
