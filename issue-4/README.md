# Issue #4 — Claude PR Review Agent

## Usage (CLI)
```bash
chmod +x issue-4/claude-review
issue-4/claude-review --pr https://github.com/owner/repo/pull/123
```

## Output Format
- Summary (2–3 sentences)
- Risks (list)
- Improvement Suggestions (list)
- Confidence (Low/Medium/High)

## GitHub Action
Use `.github/workflows/claude-pr-review.yml` with `workflow_dispatch` and `pr_url` input.

## Test Outputs
Two real-format sample outputs are in `issue-4/examples/`.
