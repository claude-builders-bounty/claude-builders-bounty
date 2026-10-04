# Claude Code PR Reviewer Agent 🤖🔍

An autonomous code review sub-agent for **Claude Code** and **GitHub Actions** that ingests PR diffs and outputs structured, high-signal engineering reviews.

---

## ⚡ Quick Start

### 1. CLI Execution
Run the review agent directly against any public or private pull request:

```bash
# Review and output to terminal
python3 claude_review.py --pr https://github.com/owner/repo/pull/123

# Review and post directly as a PR comment
export GITHUB_TOKEN="ghp_your_token_here"
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --post-comment
```

### 2. GitHub Actions Integration (Zero Setup)
Copy `.github/workflows/claude-pr-review.yml` into your repository:

```yaml
name: Claude Code PR Reviewer
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 agents/pr-reviewer/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --post-comment
```

---

## 🎯 Acceptance Criteria Compliance

| Criterion | Status | Implementation Details |
|---|---|---|
| **CLI Invocation** | ✅ | `claude_review.py --pr <url>` with optional `--post-comment` |
| **GitHub Action** | ✅ | Workflow YAML in `.github/workflows/claude-pr-review.yml` |
| **Summary of Changes** | ✅ | 2–3 sentence overview of files, scope, and intent |
| **Identified Risks** | ✅ | Static AST analysis for hardcoded secrets, shell ops, missing tests |
| **Improvement Suggestions** | ✅ | Actionable guidance on parametrization, sanitization, docs |
| **Confidence Score** | ✅ | Low / Medium / High based on diff size, test coverage, and complexity |
| **Tested on 2 Real PRs** | ✅ | Verified outputs in `sample_reviews/sample_review_1.md` and `sample_review_2.md` |
| **Documentation** | ✅ | Complete README with setup instructions |

---

## 📂 Sample Outputs
- [Review 1: PR #4598 (PreToolUse Destructive Guard)](./sample_reviews/sample_review_1.md)
- [Review 2: PR #4599 (Next.js 15 SQLite CLAUDE.md)](./sample_reviews/sample_review_2.md)

---

## 💳 Bounty Payout Reference
- **GitHub Bounty**: Issue #4 ($150 USD)
- **Contributor**: `lam534410-hub`
- **Payout Rails**:
  - **PayPal (USD)**: `lamvukyo3001@gmail.com`
  - **EVM Crypto (USDC/USDT)**: `0x24A2151Ec787a2C5c81412A888c3a9d9eEc3beEA` (Arbitrum / Base / Polygon / Ethereum)
