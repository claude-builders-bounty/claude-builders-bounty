# Claude Review Agent

Structured PR review helper for GitHub pull requests.

## CLI usage

```bash
python scripts/claude_review.py --pr https://github.com/owner/repo/pull/123
```

or:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

Optional output file:

```bash
python scripts/claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output format

- Summary of changes (2–3 sentences)
- Identified risks (list)
- Improvement suggestions (list)
- Confidence score: Low / Medium / High

## GitHub Action

Workflow file:

- `.github/workflows/claude-review.yml`

It runs on PR events, generates `review.md`, and posts the structured review as a PR comment.

## Tested PR outputs

- `samples/pr-review-1733.md` (claude-builders-bounty PR #1733)
- `samples/pr-review-1734.md` (claude-builders-bounty PR #1734)
