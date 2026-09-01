# Claude Code PR Reviewer Agent 🤖

A lightweight, autonomous GitHub Pull Request review agent for Claude Code that inspects PR diffs, identifies security risks, regression hazards, and code quality issues, and outputs a structured Markdown review comment.

## 🚀 Features
- **CLI & GitHub Action Support**: Run locally via command line or automatically in CI on every PR event.
- **Risk Analysis**: Detects hardcoded secrets, arbitrary code/command injection, SQL injection, path traversal, disabled SSL verification, and missing tests.
- **Structured Markdown Output**: Summary of changes, severity-ranked risks, actionable suggestions, and confidence score.
- **Zero Heavy Dependencies**: Uses standard Python libraries and standard GitHub REST APIs.

---

## 💻 CLI Usage

```bash
# Analyze a public PR and print markdown
python3 claude_review.py --pr https://github.com/owner/repo/pull/123

# Save markdown output to a file
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md

# Post review directly to the PR (requires GITHUB_TOKEN)
export GITHUB_TOKEN="ghp_xxx"
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --post
```

---

## ⚡ GitHub Action Integration

Add `.github/workflows/claude-review.yml` to your repository:

```yaml
name: "Claude PR Code Review"

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Run Claude PR Reviewer
        uses: ./
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          pr_url: ${{ github.event.pull_request.html_url }}
          post_comment: "true"
```

---

## 🧪 Running Unit Tests

```bash
python3 -m unittest test_reviewer.py
```
