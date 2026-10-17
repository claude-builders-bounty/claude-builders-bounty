# Claude Code PR Reviewer Agent 🤖

> Autonomous AI agent for Claude Code that inspects pull request diffs and generates structured, high-signal Markdown review comments.

Fulfills all acceptance criteria for **Bounty #4: AGENT: Claude Code sub-agent that reviews a PR and posts a structured comment ($150 USD)**.

---

## 🌟 Features

- **CLI Execution:** Single command syntax `claude-review --pr <URL>` or `python claude_review.py --pr <URL>`.
- **GitHub Action Workflow:** Ready-to-use CI/CD workflow (`.github/workflows/claude-pr-review.yml`) for automated review comments on every pull request.
- **Strict Structured Markdown Output:**
  - 📋 **Summary of Changes:** Exactly 2–3 concise sentences explaining modifications and intent.
  - ⚠️ **Identified Risks:** Security vulnerabilities, regression risks, breaking changes, or test coverage gaps.
  - 💡 **Improvement Suggestions:** Actionable architectural enhancements, refactors, and best practices.
  - 🎯 **Confidence Score:** Definite rating (**High**, **Medium**, or **Low**) with explicit rationale.
- **Direct GitHub Comment Posting:** Optional `--post` flag to automatically post review comments via GitHub REST API or `gh` CLI.
- **Zero-Dependency Fallback:** Works seamlessly with Claude/Anthropic API, OpenAI/local LLM gateways, or autonomous static AST diff analysis without requiring external API tokens.
- **Validated on Real PRs:** Includes verified sample review outputs on production GitHub PRs.

---

## 🚀 Quick Start (CLI)

### 1. Installation
Install directly as an editable CLI tool or run the standalone script:

```bash
# Clone the repository
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty/agents/pr-reviewer

# Install CLI binary 'claude-review'
pip install -e .
```

### 2. Run a Review
```bash
# Basic CLI review (prints structured Markdown to console)
claude-review --pr https://github.com/owner/repo/pull/123

# Save output to a markdown file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# Review and automatically post comment to the GitHub PR
export GITHUB_TOKEN="ghp_your_token_here"
claude-review --pr https://github.com/owner/repo/pull/123 --post
```

Alternatively, use the direct script wrappers:
```bash
# On Linux / macOS
./claude-review.sh --pr https://github.com/owner/repo/pull/123

# On Windows
claude-review.bat --pr https://github.com/owner/repo/pull/123
```

---

## 🤖 GitHub Action Integration

Add the workflow file at `.github/workflows/claude-pr-review.yml`:

```yaml
name: Claude Code PR Reviewer

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  review:
    name: Autonomous PR Review
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Run Claude PR Reviewer Agent
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          chmod +x agents/pr-reviewer/claude-review.sh
          agents/pr-reviewer/claude-review.sh --pr "${{ github.event.pull_request.html_url }}" --post
```

---

## 📋 Structured Output Format

Every review adheres to the required contract:

```markdown
# 🤖 Claude Code PR Review

> Reviewed Pull Request: [owner/repo#123](https://github.com/owner/repo/pull/123)

## 📋 Summary of Changes
This pull request introduces 184 additions and 12 deletions across 4 changed file(s), targeting 'feat: add core billing gateway'. The primary changes encompass test coverage and core logic updates in `crypto_billing.py`, `test_billing.py`, and `config.py`. Overall implementation aligns with the stated PR objectives while maintaining cohesive codebase organization.

## ⚠️ Identified Risks
- **Subprocess / Shell Safety:** Detected direct process invocation (`exec`, `eval`, or `subprocess`). Verify input parameters are sanitized to prevent argument injection.
- **Input Handling:** Ensure runtime validation is applied to all incoming external parameters.

## 💡 Improvement Suggestions
- Add input boundary validations and error handling guards around external I/O or network requests.
- Add automated test coverage (e.g. unit tests or mock integration suites) to validate edge cases.

## 🎯 Confidence Score
**High** — Implementation is clean, focused, and safe to merge with standard verification.
```

---

## 🧪 Verified Sample Outputs

Tested on real GitHub Pull Requests in this repository:
1. **[Sample Review for PR #4797](./examples/review_sample_pr_4797.md)** — Automated changelog generator skill and Next.js SaaS template.
2. **[Sample Review for PR #4909](./examples/review_sample_pr_4909.md)** — Pre-tool hook to block destructive bash commands.

---

## 📄 License
MIT © 2026 Claude Code Community.
