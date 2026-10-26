# Claude Code PR Reviewer Sub-Agent

An autonomous PR review sub-agent and GitHub Action that inspects Pull Request diffs, performs static security/risk analysis, and outputs structured Markdown review comments.

---

## ⚡ Features
- **CLI & GitHub Action Support**: Execute locally against any public or private GitHub PR or embed directly into CI/CD workflows.
- **Deep Security Risk Scanner**: Automatically detects leaked credentials (API keys, RSA keys, tokens), destructive commands (`rm -rf`, `DROP TABLE`), unparameterized SQL strings, and dangerous shell execution.
- **Actionable Markdown Feedback**: Generates structured reviews with:
  - 📝 **Summary of Changes**: 2–3 sentences highlighting the scope and impact.
  - ⚠️ **Identified Risks**: Severity-rated vulnerability items with line snippets.
  - 💡 **Improvement Suggestions**: Actionable architectural recommendations.
  - 🎯 **Confidence Score**: Calibrated Low / Medium / High assessment.

---

## 🚀 Quickstart Usage

### 1. Run via CLI
```bash
# Review public or private PR
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123

# Post comment directly to GitHub PR (requires GITHUB_TOKEN)
export GITHUB_TOKEN="ghp_your_token_here"
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123 --post-comment

# Review a local patch or diff file
python agents/pr-reviewer/claude_review.py --diff path/to/feature.patch
```

### 2. Embed into GitHub Actions (`.github/workflows/claude-review.yml`)
```yaml
name: "Claude Code PR Review"
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./agents/pr-reviewer
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          post-comment: "true"
```

---

## 📁 Real PR Review Samples
- [`samples/sample_review_1.md`](samples/sample_review_1.md): Real review of PR #5055.
- [`samples/sample_review_2.md`](samples/sample_review_2.md): Real review of PR #5058.

---

## 🧪 Automated Test Suite
```bash
python tests/test_claude_review.py
```
