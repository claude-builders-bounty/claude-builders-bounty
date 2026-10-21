# Claude Code PR Reviewer Agent

Automated pull request code review agent built for Claude Code CLI and GitHub Actions CI.

## Features
- **CLI & GitHub Action Ready:** Execute locally via `claude-review --pr <URL>` or automatically on pull request events.
- **Structured Markdown Output:**
  - Summary of changes (2–3 sentences)
  - Identified risks (security, footprint, invariants)
  - Improvement suggestions
  - Confidence score (Low / Medium / High)
- **Zero-Dependency Core:** Implemented with Python 3 standard library (`urllib`, `re`, `argparse`).

## Installation & Setup
1. Clone or copy `agents/claude-review/` into your project.
2. Ensure Python 3.8+ is installed.

## Usage

### CLI Execution
```bash
python agents/claude-review/claude_review.py --pr https://github.com/owner/repo/pull/123
```
With GitHub Token (recommended for private repos / high API rate limits):
```bash
GITHUB_TOKEN=ghp_xxx python agents/claude-review/claude_review.py --pr https://github.com/owner/repo/pull/123
```

### GitHub Action Setup
Copy `.github/workflows/claude-review.yml` into your repository. The workflow will automatically trigger on opened or updated PRs and post review comments using the default `GITHUB_TOKEN`.
