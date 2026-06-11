# Bounty #4 Proof

Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4

## Acceptance Criteria

- Works via CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
  - Implemented in `bin/claude-review.js`.
  - Uses GitHub PR `.diff` URLs and follows redirects.

- OR via GitHub Action
  - Included optional workflow: `.github/workflows/claude-review.yml`.

- Structured Markdown output
  - Output sections:
    - Summary
    - Identified Risks
    - Improvement Suggestions
    - Confidence

- Tested on at least 2 real GitHub PRs
  - `samples/vercel-next-93553-review.md`
  - `samples/vercel-next-93260-review.md`

- README with setup and usage
  - Main README includes quick usage.
  - Extended docs in `docs/claude-review-agent.md`.

- Claude Code sub-agent
  - Agent instructions included in `.claude/agents/pr-reviewer.md`.

## Validation

```bash
npm run check
```

This runs unit tests, generates a sample review from fixture diff, and checks diff whitespace.
