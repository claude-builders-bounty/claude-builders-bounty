# Claude Code PR Reviewer Agent (`claude-review`) (#4)

> 💰 Bounty: $150 — powered by [Opire](https://opire.dev)

An autonomous Claude Code agent and CLI tool that ingests GitHub PR diffs, conducts senior-level architectural and security analysis using the Claude API (`claude-sonnet-4-20250514`), and produces structured, actionable Markdown reviews.

---

## 🚀 Features

- **CLI Execution**: Inspect any PR directly via `claude-review --pr https://github.com/owner/repo/pull/123`.
- **GitHub Action Workflow**: Seamless CI/CD integration that automatically comments on new and updated PRs.
- **Strictly Structured Output**:
  - 📝 **Summary of Changes**: 2–3 sentence executive summary.
  - ⚠️ **Identified Risks**: Security, performance, breaking changes, and regression risks.
  - 💡 **Improvement Suggestions**: Actionable architectural and testing recommendations.
  - 🎯 **Recommendation & Confidence**: Clear `APPROVE`, `REQUEST_CHANGES`, or `COMMENT` verdict with a confidence rating (`Low`, `Medium`, `High`).
- **Direct GitHub Posting**: Posts the review comment directly to the PR with `--post` when `GITHUB_TOKEN` is provided.

---

## 📦 Installation & Setup

```bash
# Clone and install in editable mode
cd agents/pr-reviewer
pip install -e .
```

Ensure environment variables are exported:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..." # Optional for public PRs, required for private repos or --post
```

---

## 💻 CLI Usage Examples

### 1. Review a Pull Request (Print to Terminal)
```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

### 2. Review and Post Comment Directly to GitHub
```bash
claude-review --pr https://github.com/owner/repo/pull/123 --post
```

### 3. Save Review to Markdown File
```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

### 4. Custom Model Selection
```bash
claude-review --pr https://github.com/owner/repo/pull/123 --model claude-3-5-sonnet-20241022
```

---

## 🤖 GitHub Action Integration

Copy `.github/workflows/claude-pr-review.yml` into your repository:

```yaml
name: Claude Code PR Reviewer

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e agents/pr-reviewer
      - name: Review PR
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          claude-review --pr "${{ github.event.pull_request.html_url }}" --post
```

---

## 🧪 Testing

Run automated tests:
```bash
pytest agents/pr-reviewer/tests/test_reviewer.py -v
```
