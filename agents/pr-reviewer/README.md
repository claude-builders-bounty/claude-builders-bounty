# 🤖 Claude PR Review Sub-Agent

An automated GitHub Pull Request Review Agent that analyzes diffs, identifies architectural/security risks, and generates clean, structured Markdown review comments.

---

## ⚡ Features

- **📋 Structured Review Output**:
  - Summary of changes (2–3 sentences)
  - Identified risks (DB schema migrations, auth logic, PR size, dependencies)
  - Improvement suggestions & test coverage recommendations
  - Confidence Score (`High` / `Medium` / `Low`)
- **💻 CLI & CI/CD Support**: Run locally via command-line or plug directly into GitHub Actions.
- **⚡ Zero-Config**: Works out of the box with standard Python 3.

---

## 🚀 CLI Usage

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

With optional output to file:
```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

---

## 🔄 GitHub Action Integration

Add `.github/workflows/claude-review.yml` to your repository:

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run Review Agent
        run: |
          python3 claude_review.py --pr ${{ github.event.pull_request.html_url }} --token ${{ secrets.GITHUB_TOKEN }} --output review.md
      - name: Post PR Comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const body = fs.readFileSync('review.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

---

## 🧪 Verified Real PR Outputs

### 1. Review on `apify/crawlee` (PR #4048)
```markdown
### 🤖 Automated Claude PR Review

#### 📋 Summary of Changes
This pull request **'chore(deps): update dependency puppeteer to v25.8.0'** by @B4nan modifies **2 files** (+53/-57 lines). The changes focus on core implementation updates and related feature logic across the codebase.

#### ⚠️ Identified Risks
- No critical architectural risks detected. Standard changes within normal parameters.

#### 💡 Improvement Suggestions
- Code structure follows standard conventions. Ensure CI pipeline passes cleanly.

---
**Confidence Score**: `High` | **Files Reviewed**: `2`
```
