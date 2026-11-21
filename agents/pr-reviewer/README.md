# Claude Code Sub-Agent: Structured PR Reviewer (`claude-review`) — Bounty Issue #4

Analyzes any GitHub Pull Request diff via CLI (`claude-review --pr https://github.com/owner/repo/pull/123`) or GitHub Actions (`claude-review.yml`) and outputs a structured Markdown review containing a 2–3 sentence summary, identified risks, improvement suggestions, and a confidence score (`Low` / `Medium` / `High`).

## Setup & Usage (3 Steps)

1. `chmod +x claude-review`
2. `./claude-review --pr https://github.com/colinhacks/zod/pull/6772`
3. Copy `claude-review.yml` to `.github/workflows/claude-review.yml` to auto-review every PR.

## Tested Sample Outputs (2 Real GitHub PRs)

See [`SAMPLE_REVIEWS.md`](./SAMPLE_REVIEWS.md) for full real CLI captures run against `colinhacks/zod#6772` and `vercel/next.js#102172`.
