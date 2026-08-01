# Sample PR Reviews

These are real outputs from `claude-review.py` run against two actual PRs in the `claude-builders-bounty/claude-builders-bounty` repository:

| File | Source PR | Bounty |
|---|---|---|
| [`review-pr-3651.md`](./review-pr-3651.md) | [PR #3651](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3651) — feat: add generate-changelog skill | #1 ($50) |
| [`review-pr-3652.md`](./review-pr-3652.md) | [PR #3652](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3652) — feat(hook): PreToolUse hook to block destructive bash commands | #3 ($100) |

## Reproducing

```bash
# Review PR #3651
python ../claude-review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3651 > review-pr-3651.md

# Review PR #3652
python ../claude-review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3652 > review-pr-3652.md
```

Requires `ANTHROPIC_API_KEY` in the environment.

## What the reviews demonstrate

- **Structured Markdown output** with Summary / Risks / Suggestions / Confidence sections (per the bounty spec)
- **Specific, actionable suggestions** that reference the actual diff content
- **Calibrated confidence scoring** (High / Medium / Low with justification)
- **Identifies real issues** like missing log rotation, dry-run mode, edge cases in regex
