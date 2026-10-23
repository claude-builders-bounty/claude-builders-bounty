# Claude Code PR Reviewer Agent

> An automated PR reviewer agent for Claude Code that fetches GitHub pull request diffs, performs semantic and risk analysis, and produces structured Markdown review comments.

---

## 🚀 Quick Start (CLI)

Run directly on any public or private GitHub PR:

```bash
python agents/pr-reviewer/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --token "$GITHUB_TOKEN"
```

### Options
- `--pr <URL>`: Required. Full URL of the GitHub pull request.
- `--token <TOKEN>`: GitHub Personal Access Token (defaults to `GITHUB_TOKEN` environment variable).
- `--comment`: Posts the review markdown directly as a comment on the PR.
- `--output <FILE>`: Saves the Markdown review to the specified file path.

---

## ⚡ GitHub Actions Integration

To automatically review every incoming pull request in your repository, add `.github/workflows/claude-review.yml`:

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
    name: Automated AI PR Review
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: |
          python agents/pr-reviewer/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --token "${{ secrets.GITHUB_TOKEN }}" \
            --comment
```

---

## 📊 Structured Markdown Output Format

Every review generated follows this exact schema:

1. **Summary of Changes**: Concise 2-3 sentence overview of files changed, intent, and whether automated tests are included.
2. **Identified Risks**: Catches hardcoded credentials, destructive shell commands (`rm -rf`), SQL injection patterns, and excessive diff volumes.
3. **Improvement Suggestions**: Actionable code quality, typing, and testing suggestions.
4. **Confidence Score**: Deterministic confidence rating (**High**, **Medium**, **Low**) based on risk heuristics and test presence.

---

## 📁 Sample Outputs from Real PRs

Check the `samples/` directory for verified real-world reviews:
- [`samples/sample_review_1.md`](samples/sample_review_1.md): Real review of PR #5018.
- [`samples/sample_review_2.md`](samples/sample_review_2.md): Real review of PR #5019.

---

## 🧪 Running the Tests

```bash
pytest tests/test_claude_review.py -v
```
