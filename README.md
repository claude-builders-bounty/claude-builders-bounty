# Claude PR Review Agent

CLI/GitHub Action agent for bounty #4. It reviews a pull request diff and prints a structured Markdown review comment.

## CLI usage

```bash
npm install
node bin/claude-review.js --pr https://github.com/owner/repo/pull/123
```

Optional env:

- `ANTHROPIC_API_KEY`: enables Claude-powered review.
- `GITHUB_TOKEN`: used by `gh` for private repos or higher rate limits.

Without `ANTHROPIC_API_KEY`, the CLI still produces a deterministic structured fallback review from the diff stats.

## Output format

- Summary of changes, 2-3 sentences
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

## GitHub Action

Copy `.github/workflows/claude-review.yml` into a repo. It runs on PRs and posts the generated review as a comment.
