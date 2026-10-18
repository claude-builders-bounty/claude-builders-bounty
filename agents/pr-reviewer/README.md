# Claude Code PR Reviewer Sub-Agent 🤖

> Automated Pull Request reviewer agent that inspects diffs, evaluates risks, and posts structured Markdown reviews.

[![Bounty](https://img.shields.io/badge/bounty-%24150-success)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)
[![Tests](https://img.shields.io/badge/tests-3%2F3%20passed-brightgreen)](#testing)

---

## ⚡ Quick Start (CLI)

```bash
# Review a PR and output structured Markdown
python3 agents/pr-reviewer/claude_review.py \
  --pr https://github.com/owner/repo/pull/123

# Review and automatically post comment to the PR
python3 agents/pr-reviewer/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --post
```

---

## 🚀 GitHub Action Integration

Copy `.github/workflows/claude-review.yml` into your repository:

```yaml
name: Claude Code PR Reviewer
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: |
          python3 agents/pr-reviewer/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --post
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 📋 Structured Output Format

Every review includes:
1. **Summary of Changes**: Concise 2–3 sentence overview of scope and impacted files.
2. **Identified Risks**: Heuristic audit for exposed secrets, destructive commands, or binary blobs.
3. **Improvement Suggestions**: Actionable recommendations for test coverage and documentation.
4. **Confidence Score**: High / Medium / Low rating based on review heuristics.

---

## 📄 Real PR Sample Outputs

Verified on real GitHub PRs:
- [Sample Review for PR #4930](sample_reviews/review_pr_4930.md)
- [Sample Review for PR #4931](sample_reviews/review_pr_4931.md)

---

## 🧪 Testing

```bash
python3 agents/pr-reviewer/test_reviewer.py
```
