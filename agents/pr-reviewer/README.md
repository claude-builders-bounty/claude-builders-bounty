# Claude Code PR Reviewer Sub-Agent 🔍

An autonomous sub-agent and GitHub Action that analyzes Pull Request diffs, identifies architectural/security risks, calculates confidence scores, and posts structured Markdown review comments.

---

## ⚡ CLI Usage

```bash
# Review any public GitHub PR
node agents/pr-reviewer/pr_reviewer.js --pr https://github.com/owner/repo/pull/123

# Review a local diff file
node agents/pr-reviewer/pr_reviewer.js --diff changes.diff

# Authenticated review with GitHub Token
node agents/pr-reviewer/pr_reviewer.js --pr https://github.com/owner/repo/pull/123 --token $GITHUB_TOKEN
```

---

## 🤖 GitHub Action Setup

Add `.github/workflows/pr-review.yml` to your repository:

```yaml
name: Claude PR Reviewer
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: node agents/pr-reviewer/pr_reviewer.js --pr "${{ github.event.pull_request.html_url }}" --token "${{ secrets.GITHUB_TOKEN }}"
```

---

## 🧪 Testing

```bash
node --test agents/pr-reviewer/tests/test_reviewer.js
```
