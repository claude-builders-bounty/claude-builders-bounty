# 🤖 Claude Code PR Reviewer Agent (`claude-review`)

An automated PR review sub-agent that fetches unified diffs from GitHub Pull Requests, analyzes code quality and architectural risks, and generates structured Markdown reviews with confidence scoring.

---

## ⚡ Features

- 🔍 **Deep Static Diff Analysis**:
  - Detects hardcoded credentials & API secrets.
  - Flags unhandled asynchronous/Promise rejections.
  - Detects SQL string interpolation risks.
  - Evaluates test coverage ratios and changeset blast radiuses.
- 📋 **Structured Markdown Output**:
  - **Summary of changes**: 2–3 clear sentences summarizing the scope and intent.
  - **Identified risks**: Actionable list of flagged security or stability concerns.
  - **Improvement suggestions**: Targeted recommendations for maintainers.
  - **Confidence score**: Evaluated as `High`, `Medium`, or `Low`.
- 🚀 **Dual Execution Modes**:
  - **CLI**: Run directly on any terminal.
  - **GitHub Actions**: Automatically comment on new and updated Pull Requests.

---

## 💻 CLI Usage

```bash
# Make binary executable
chmod +x agents/pr-reviewer/bin/claude-review

# Review a pull request and print output
./agents/pr-reviewer/bin/claude-review --pr https://github.com/owner/repo/pull/123

# Save review to a file
./agents/pr-reviewer/bin/claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# Review and post comment directly to GitHub
export GITHUB_TOKEN="ghp_xxx"
./agents/pr-reviewer/bin/claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

---

## ⚙️ GitHub Action Integration

Copy `.github/workflows/pr-review.yml` to your repository:

```yaml
name: Claude Code Automated PR Review

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

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run Claude Code PR Reviewer
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          chmod +x agents/pr-reviewer/bin/claude-review
          python3 agents/pr-reviewer/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --post-comment \
            --token "${{ secrets.GITHUB_TOKEN }}"
```

---

## 🧪 Testing

```bash
python3 agents/pr-reviewer/test_review.py
```
Output:
```
Ran 4 tests in 0.001s
OK
```

---

## 📄 Real GitHub PR Review Samples

- [Sample Review 1 (PR #4301)](samples/sample_review_1.md)
- [Sample Review 2 (PR #4302)](samples/sample_review_2.md)
