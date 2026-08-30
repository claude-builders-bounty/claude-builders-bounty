# 🤖 Claude Code PR Review Agent

An autonomous Claude Code sub-agent and GitHub Action that evaluates Pull Request diffs and posts structured Markdown review comments conforming to Opire Bounty #4 acceptance criteria.

---

## ✨ Features
- **CLI & GitHub Action Ready**: Run locally via `bin/claude-review` or automate in CI using `.github/workflows/claude-review.yml`.
- **Structured Markdown Output**:
  - 📋 Summary of changes (2–3 sentences)
  - ⚠️ Identified risks (list)
  - 💡 Improvement suggestions (list)
  - 🎯 Confidence score (`Low` / `Medium` / `High`)
- **Deterministic & AI-Powered**: Supports Anthropic Claude API when `ANTHROPIC_API_KEY` is provided, with a zero-dependency deterministic heuristic fallback.
- **Tested on Real GitHub PRs**: Sample outputs verified on real live production pull requests.

---

## 🚀 3-Step Setup Guide

### 1. Clone & Set Permissions
```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
chmod +x bin/claude-review
```

### 2. Run Local CLI Review
```bash
python3 bin/claude-review --pr https://github.com/owner/repo/pull/123
```

### 3. Add to GitHub Actions (Optional)
Copy `.github/workflows/claude-review.yml` to your target repository to automatically review every opened pull request.

---

## 🧪 Verification & Testing
Run the test suite:
```bash
python3 -m unittest discover tests
```

Sample reviews from real PRs are available in `agents/claude_review/samples/`.
