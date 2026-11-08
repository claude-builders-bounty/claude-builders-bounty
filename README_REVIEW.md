# Claude Code PR Review Agent

An autonomous PR review tool and GitHub Action that analyzes pull request diffs and generates structured, actionable Markdown review comments.

This tool solves **Issue #4 ($150 USD Bounty)** for `claude-builders-bounty/claude-builders-bounty`.

---

## 🚀 Features

- **CLI Interface**: Inspect any pull request instantly via CLI:
  ```bash
  python claude_review.py --pr https://github.com/owner/repo/pull/123
  ```
- **Automated GitHub Action**: Runs automatically on PR open/synchronize, analyzing changes and posting comments directly.
- **Structured Markdown Output**:
  1. **Summary of Changes**: Concise 2–3 sentence overview of files, additions, and deletions.
  2. **Identified Risks**: Detects credential leaks, CI/dependency modifications, high deletion volume, or missing test coverage.
  3. **Improvement Suggestions**: Actionable recommendations for maintainability, documentation, and testing.
  4. **Confidence Score**: Deterministic evaluation (`Low` / `Medium` / `High`).
- **Real-World Tested**: Validated against real open-source pull requests.

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- GitHub CLI (`gh`) installed and authenticated (`gh auth login`)

### Usage

1. **Review a PR in terminal**:
   ```bash
   python claude_review.py --pr https://github.com/owner/repo/pull/123
   ```

2. **Save review to a file**:
   ```bash
   python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
   ```

3. **Review and automatically post comment to PR**:
   ```bash
   python claude_review.py --pr https://github.com/owner/repo/pull/123 --post-comment
   ```

---

## 📦 GitHub Actions Workflow Integration

Include `.github/workflows/claude-review.yml` in your repository:

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
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run Claude Code PR Review Agent
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python claude_review.py --pr "${{ github.event.pull_request.html_url }}" --post-comment
```

---

## 📊 Sample Outputs (Tested on Real GitHub PRs)

### Sample 1: `Peter7896/TentOfTrials#42`
See [sample_reviews/sample_review_1.md](sample_reviews/sample_review_1.md)

### Sample 2: `jackjin1997/zeroeye#27`
See [sample_reviews/sample_review_2.md](sample_reviews/sample_review_2.md)
