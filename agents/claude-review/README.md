# Claude PR Review Sub-Agent 🔍

An automated PR review sub-agent for Claude Code that analyzes Pull Request diffs, identifies security risks, missing test coverage, and destructive patterns, and publishes structured Markdown review comments.

Bounty #4 submission for **Claude Builders Bounty** ($150 — powered by Opire).

---

## 📋 Features & Acceptance Criteria Checklist
- [x] **CLI Invocation**: Run `python3 claude_review.py --pr https://github.com/owner/repo/pull/123`.
- [x] **GitHub Action Integration**: Reusable workflow included at `workflows/claude-review.yml`.
- [x] **Structured Markdown Output**:
  - Summary of changes (2–3 sentences)
  - Identified risks (credentials leak, destructive commands, missing tests)
  - Improvement suggestions
  - Confidence score (`High` / `Medium` / `Low`)
- [x] **Tested on real GitHub PRs**: Sample review outputs included in `examples/review_pr_4408.md` and `examples/review_pr_4409.md`.
- [x] **Zero Dependencies**: Pure standard library Python 3.

---

## ⚡ Quick Setup & Usage

### Option A: Local CLI Usage
```bash
# Set your GitHub token (optional for public repos, recommended to avoid rate limits)
export GITHUB_TOKEN="ghp_your_token_here"

# Run review on any PR
python3 agents/claude-review/claude_review.py --pr https://github.com/owner/repo/pull/123

# Run review and automatically post comment to the PR
python3 agents/claude-review/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --post-comment
```

### Option B: GitHub Actions Workflow
Add `.github/workflows/claude-review.yml` to your repository:
```yaml
name: Claude PR Review
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
          python-version: '3.11'
      - name: Review PR
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 agents/claude-review/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --post-comment
```

---

## 🧪 Testing

Run the automated test suite:
```bash
python3 agents/claude-review/tests/test_claude_review.py
```
