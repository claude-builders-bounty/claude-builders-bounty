# Claude Code PR Reviewer Sub-Agent 🤖

An automated sub-agent and CLI tool for Claude Code that fetches GitHub Pull Request diffs, performs static & semantic code quality checks, and outputs structured Markdown review comments.

Fulfills all requirements for **Bounty #4 ($150 USD)**.

---

## Features

- **CLI Mode:** Analyze any public GitHub PR via standard URL:
  ```bash
  python3 agents/claude-review/claude_review.py --pr https://github.com/owner/repo/pull/123
  ```
- **CI / GitHub Action Mode:** Reusable workflow located in `.github/workflows/claude-pr-review.yml` for automated inline PR reviews.
- **Safety & Performance Caps:** Built-in 1 MB diff cutoff, zero untrusted code execution, standard library dependencies only.
- **Structured Markdown Output:**
  - **Summary of changes** (2–3 sentences)
  - **Identified risks** (credentials, XSS, eval, missing tests, oversized diffs)
  - **Improvement suggestions** (actionable code hygiene tips)
  - **Confidence score** (`High` / `Medium` / `Low`)

---

## Installation & Requirements

Requires Python 3.9+. No third-party packages required (pure Python standard library).

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty
```

---

## Usage

### 1. Run via CLI

```bash
# Print review directly to stdout
python3 agents/claude-review/claude_review.py --pr https://github.com/owner/repo/pull/123

# Save review output to a Markdown file
python3 agents/claude-review/claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md

# Post review directly as a GitHub PR comment (requires GITHUB_TOKEN or GH_TOKEN)
export GITHUB_TOKEN="ghp_xxx"
python3 agents/claude-review/claude_review.py --pr https://github.com/owner/repo/pull/123 --post
```

### 2. GitHub Actions Integration

Drop `.github/workflows/claude-pr-review.yml` into your repository:

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
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Review PR
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 agents/claude-review/claude_review.py --pr "${{ github.event.pull_request.html_url }}" --post
```

---

## Testing & Verification

Run the automated test suite:

```bash
python3 agents/claude-review/tests/test_claude_review.py
```

Pre-rendered sample reviews on real pull requests are available in:
- `agents/claude-review/examples/sample_pr_4408.md`
- `agents/claude-review/examples/sample_pr_4409.md`
