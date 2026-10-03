# Claude Code PR Reviewer Agent

A sub-agent for Claude Code that inspects Pull Request diffs and posts structured Markdown review comments.

## Features
- CLI command support: `python3 agent/claude_review.py --pr <PR_URL> [--post-comment]`
- GitHub Action integration (`.github/workflows/claude-review.yml`)
- Outputs structured Markdown containing:
  - 📝 Summary of changes (2-3 sentences)
  - ⚠️ Identified risks
  - 💡 Improvement suggestions
  - 🎯 Confidence score (Low / Medium / High)

## Setup & Usage

### 1. CLI Usage
Run directly from terminal:
```bash
python3 agent/claude_review.py --pr https://github.com/owner/repo/pull/123
```
To post the comment to GitHub directly (requires `gh` CLI authenticated):
```bash
python3 agent/claude_review.py --pr https://github.com/owner/repo/pull/123 --post-comment
```

### 2. GitHub Actions Integration
Include `.github/workflows/claude-review.yml` in your repository. It automatically executes on newly opened PRs or commits, leaving a review comment using `GITHUB_TOKEN`.

---

## Sample Review Outputs

### Sample 1: `paraloom-labs/paraloom-wallet/pull/33`
```markdown
## 🤖 Claude Code Automated PR Review

### 📝 Summary of Changes
This pull request modifies 2 file(s) with +88 / -15 line changes in `paraloom-labs/paraloom-wallet`. The updates primarily address target logic and workflow configurations across the affected components.

### ⚠️ Identified Risks
- Possible hardcoded secret or sensitive credentials in added statements.

### 💡 Improvement Suggestions
- Ensure type coverage and automated linter passes are enforced on all modified modules.
- Review CI/CD workflow status to ensure all hermetic checks succeed.

### 🎯 Confidence Score
**High**
```

### Sample 2: `claude-builders-bounty/claude-builders-bounty/pull/4667`
```markdown
## 🤖 Claude Code Automated PR Review

### 📝 Summary of Changes
This pull request modifies 2 file(s) with +209 / -31 line changes in `claude-builders-bounty/claude-builders-bounty`. The updates primarily address target logic and workflow configurations across the affected components.

### ⚠️ Identified Risks
- Low direct regression risk observed; changes appear isolated and focused.

### 💡 Improvement Suggestions
- Consider adding or updating automated unit tests to cover the modified logic paths.
- Review CI/CD workflow status to ensure all hermetic checks succeed.

### 🎯 Confidence Score
**High**
```
