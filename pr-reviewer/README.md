# claude-review — GitHub PR Reviewer

A zero-dependency Python tool that fetches a GitHub PR and outputs a structured Markdown review with summary, risks, improvements, and a confidence score.

Runs as a standalone CLI or as a GitHub Action.

## Install

```bash
curl -O https://raw.githubusercontent.com/castrocrest/claude-builders-bounty-entries/main/pr-reviewer/claude_review.py
```

**Requirements:** Python 3.9+ only (no pip install needed).

## CLI Usage

```bash
# Full GitHub URL
python claude_review.py --pr https://github.com/psf/requests/pull/7500

# Shorthand: owner/repo/number
python claude_review.py --pr psf/requests/7500

# Just a number + --repo flag
python claude_review.py --pr 7500 --repo psf/requests

# Save to file
python claude_review.py --pr psf/requests/7500 --output review.md

# With a GitHub token (avoids rate limits)
GITHUB_TOKEN=ghp_xxx python claude_review.py --pr psf/requests/7500
```

## GitHub Action Usage

Add this workflow to your repo at `.github/workflows/pr-review.yml`:

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Download claude-review
        run: |
          curl -O https://raw.githubusercontent.com/castrocrest/claude-builders-bounty-entries/main/pr-reviewer/claude_review.py

      - name: Review PR
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python claude_review.py \
            --pr ${{ github.event.pull_request.html_url }} \
            --output pr-review.md
          cat pr-review.md

      - name: Post review as comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs')
            const body = fs.readFileSync('pr-review.md', 'utf8')
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.payload.pull_request.number,
              body
            })
```

## Output Format

The review is structured Markdown with four sections:

```markdown
## PR Review: [title](url)

> **author** wants to merge `branch` → `main`
> N commit(s) · M file(s) changed · +X −Y lines

---

### Summary

[PR description excerpt]

This PR touches N file(s), primarily `.py`, `.yml`. Tests are included.

**Changed files (top by size):**
- `src/main.py` (+163 −46)
- ...

**Commits:**
- `abc1234` feat: add feature
- ...

---

### Identified Risks

- ⚠️ `.github/workflows/ci.yml` — infrastructure/CI change
- ⚠️ No test file changes detected — consider adding tests

---

### Improvement Suggestions

- 💡 Add unit tests for the changed logic to prevent regressions.

---

### Confidence Score: **High**

_This PR has a description, has focused scope, has descriptive commits._
```

## What the analysis checks

| Signal | Flagged as |
|--------|-----------|
| Files with `secret`, `token`, `password`, `.pem`, `.key` in name | Risk |
| Changes to `.github/workflows/`, Dockerfile, terraform files | Risk |
| Single file change > 200 lines | Risk |
| PR has > 20 files changed | Risk |
| PR has > 500 lines added total | Risk |
| No test file changes and > 50 additions | Risk |
| PR has no description | Risk |

**Confidence score** is based on: PR has description, tests are present, focused scope (≤ 10 files), good commit messages, small diff.

## Run tests

```bash
python -m pytest tests/ -v
```

31 tests covering URL parsing, risk scoring, analysis logic, report generation, and CLI behavior.

## Sample output

- [SAMPLE_OUTPUT_1.md](SAMPLE_OUTPUT_1.md) — `psf/requests` dependabot PR
- [SAMPLE_OUTPUT_2.md](SAMPLE_OUTPUT_2.md) — `CapSoftware/Cap` memory-leak fix PR (9 commits, Rust)
