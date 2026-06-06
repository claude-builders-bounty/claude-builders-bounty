# claude-review

A Claude Code agent that reviews a GitHub PR and returns a structured Markdown comment.

## Output format

Every review contains:

- **Summary** — 2–3 sentences describing what the PR does
- **Identified Risks** — list of potential issues
- **Improvement Suggestions** — actionable recommendations
- **Confidence Score** — `Low | Medium | High` with justification

## Setup

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...   # optional but raises rate limits
```

## Usage

### CLI

```bash
python agents/claude-pr-review/claude-review --pr https://github.com/owner/repo/pull/123
```

Write to a file:

```bash
python agents/claude-pr-review/claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --output review.md
```

### GitHub Action (auto-post on every PR)

Add `ANTHROPIC_API_KEY` to your repo secrets, then the workflow at
`.github/workflows/claude-pr-review.yml` runs automatically on `pull_request`
events and posts the review as a comment.

## Sample outputs

- [`samples/review-pr2546.md`](samples/review-pr2546.md) — review of a PR review agent implementation
- [`samples/review-pr2554.md`](samples/review-pr2554.md) — review of a destructive-command hook

## Tests

```bash
python -m pytest agents/claude-pr-review/tests.py -v
# 7 passed
```
