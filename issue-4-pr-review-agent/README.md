# Claude PR Review Agent

1. Install and authenticate GitHub CLI: `gh auth login`.
2. Run `python issue-4-pr-review-agent/claude_review.py --pr https://github.com/owner/repo/pull/123`.
3. Optionally add `--output review.md` to save the Markdown, or `--post-comment` to publish it back to the PR through `gh`.

The included `.github/workflows/claude-pr-review.yml` workflow can also post the same structured comment on every opened, synchronized, or reopened pull request.

## What it does

- Fetches PR metadata and the full diff through GitHub CLI.
- Produces structured Markdown with:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence score
- Works without extra Python dependencies.

## Notes

- `gh auth login` must already be configured.
- Sample outputs for two real PRs live in `issue-4-pr-review-agent/examples/`.
- A GitHub Action wrapper can call the same script in CI.
