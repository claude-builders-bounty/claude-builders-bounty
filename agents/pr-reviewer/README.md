# Claude Code PR Reviewer Agent

An autonomous sub-agent and GitHub Action that ingests pull request diffs, performs automated architectural and security risk analysis, and outputs structured Markdown review comments.

---

## ⚡ Usage via CLI

```bash
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
```

To post the review directly to the PR:
```bash
python agents/pr-reviewer/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --token "$GITHUB_TOKEN" \
  --post
```

---

## 🤖 Usage as a GitHub Action

Add `.github/workflows/claude-review.yml`:

```yaml
name: Claude Code PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  pull-requests: write
  contents: read

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Claude Reviewer
        uses: claude-builders-bounty/claude-builders-bounty/agents/pr-reviewer@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

---

## 📋 Structured Output Schema

Every review follows this standardized Markdown format:

1. **Summary of Changes**: Concise 2–3 sentence overview of modifications and scope.
2. **Identified Risks**: Flagged security risks (e.g., credentials in diffs, unindexed SQL, unconstrained deletions, missing test coverage).
3. **Improvement Suggestions**: Actionable recommendations for code quality, typing, and testing.
4. **Confidence Score**: `High`, `Medium`, or `Low` based on file count, patch complexity, and risk heuristics.

---

## 🧪 Verified Real PR Outputs

See attached verified execution outputs on real GitHub pull requests:
- [`sample_output_pr5043.md`](sample_output_pr5043.md) (Verified against PR #5043)
- [`sample_output_pr5044.md`](sample_output_pr5044.md) (Verified against PR #5044)
