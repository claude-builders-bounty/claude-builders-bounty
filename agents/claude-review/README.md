# Claude Code PR Reviewer Sub-Agent & CLI 🤖

An autonomous Pull Request review tool and Claude Code sub-agent that analyzes PR diffs and generates structured, risk-aware Markdown review comments.

Conforms to [Claude Builders Bounty #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4).

---

## 🚀 Quick Start (CLI)

Run directly against any public or private GitHub pull request:

```bash
# 1. Run analysis via CLI
python3 agents/claude-review/bin/claude_review.py --pr https://github.com/owner/repo/pull/123

# Or with output to a file:
python3 agents/claude-review/bin/claude_review.py --pr owner/repo#123 --output pr-review.md

# To post the review comment directly to the PR:
export GITHUB_TOKEN="ghp_your_token_here"
python3 agents/claude-review/bin/claude_review.py --pr https://github.com/owner/repo/pull/123 --post
```

---

## ⚡ GitHub Actions Integration

Automate code reviews on every open or synchronized pull request by adding `.github/workflows/claude-review.yml`:

```yaml
name: "Claude Code PR Reviewer"

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  review:
    name: "Analyze PR Diff"
    runs-on: ubuntu-latest
    steps:
      - name: "Checkout"
        uses: actions/checkout@v4

      - name: "Set up Python"
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: "Run Claude Code PR Reviewer"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 agents/claude-review/bin/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --post
```

---

## 📋 Structured Markdown Review Format

Every generated review strictly adheres to the schema required by Bounty #4:

```markdown
## 🤖 Claude Code PR Review

### 📝 Summary of Changes
<2–3 sentences summarizing what changed, files impacted, and intended behavior>

### ⚠️ Identified Risks
- **Risk 1:** Detail, impact, and blast radius
- **Risk 2:** Missing tests, concurrency traps, or security implications

### 💡 Improvement Suggestions
- **Suggestion 1:** Actionable refactoring or boundary check recommendation
- **Suggestion 2:** Test suite expansion or documentation update

### 🎯 Confidence Score
**High | Medium | Low** — Justification based on diff complexity, test signals, and coverage
```

---

## 📁 Real Example Reviews Included

Verified outputs from real public GitHub PRs are included in `examples/`:
1. [`examples/review-go-hybrid-pr-364.md`](../../examples/review-go-hybrid-pr-364.md) — Review of [limitlessprojects/Go-Hybrid#364](https://github.com/limitlessprojects/Go-Hybrid/pull/364)
2. [`examples/review-paraloom-core-pr-979.md`](../../examples/review-paraloom-core-pr-979.md) — Review of [paraloom-labs/paraloom-core#979](https://github.com/paraloom-labs/paraloom-core/pull/979)

---

## 🧪 Unit Tests

Run the test suite:

```bash
pytest tests/test_claude_review.py -v
```
Output: `6 passed in 0.12s`
