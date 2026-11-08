# Claude Code PR Reviewer Agent 🤖

An autonomous sub-agent for Claude Code and CI/CD pipelines that inspects GitHub Pull Request diffs, flags security and regression risks, and outputs structured Markdown review comments.

## Features

- **Risk Invariant Engine:** Detects hardcoded secrets/JWTs, destructive bash commands (`rm -rf`, `DROP TABLE`), unbounded SQL operations, and permissive CORS bypasses.
- **Structured Markdown Output:** Summary of changes (2–3 sentences), identified risks, improvement suggestions, and calibrated confidence score.
- **Zero-Dependency CLI:** Runs seamlessly on Python 3.9+ across Linux, macOS, and Windows.
- **GitHub Action Included:** Composite workflow for automated PR review comments.

## Quickstart (3 Steps)

### 1. Review via CLI
```bash
python agents/pr-reviewer/reviewer.py --pr https://github.com/owner/repo/pull/123
```

### 2. Save Markdown Output to File
```bash
python agents/pr-reviewer/reviewer.py --pr https://github.com/owner/repo/pull/123 --output pr_review.md
```

### 3. Run Automated Tests
```bash
python agents/pr-reviewer/tests/test_reviewer.py
```

## GitHub Action Usage
Add the step to your `.github/workflows/review.yml`:
```yaml
- name: Automated PR Review
  uses: ./agents/pr-reviewer
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```
