# Claude Code PR Review Sub-Agent

A dedicated sub-agent for [Claude Code](https://docs.anthropic.com/claude-code) and GitHub Actions that analyzes Pull Request diffs and posts structured, high-signal Markdown review comments.

## Features
- **Structured Markdown Output**: Generates 2–3 sentence change summaries, identified risks, improvement suggestions, and a confidence score (Low / Medium / High).
- **Dual Execution Modes**: Works locally via CLI or automatically in CI via GitHub Actions.
- **Zero Heavy Dependencies**: Built with Python 3 standard library (`urllib`, `re`, `json`).

---

## 1. CLI Usage

Run the review agent directly against any public GitHub pull request:
```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```
Or save the review to a file:
```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

*(Optional: Set `export GITHUB_TOKEN=ghp_...` for private repositories or higher GitHub API rate limits).*

---

## 2. GitHub Actions Integration

Drop `.github/workflows/claude-review.yml` into your repository. Whenever a pull request is opened or updated, the action automatically inspects the diff and comments the review directly on the PR.

---

## 3. Verified Sample Outputs

See the `sample-outputs/` directory for verified real-world PR reviews:
- [Sample 1: facebook/react#28001](sample-outputs/pr-review-sample-1.md)
- [Sample 2: vercel/next.js#62015](sample-outputs/pr-review-sample-2.md)
