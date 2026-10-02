# 🤖 Claude PR Review Agent (CLI & GitHub Action)

A sub-agent for Claude Code that analyzes pull request diffs, checks for security regressions, missing tests, and maintainability concerns, and formats structured Markdown review comments with risk indicators and confidence scores.

---

## ⚡ Quickstart (3 Steps or Fewer)

1. **Clone & Navigate**:
   ```bash
   git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
   cd claude-builders-bounty/agents/claude-pr-review
   ```

2. **Run PR Review**:
   ```bash
   ./claude-review --pr https://github.com/owner/repo/pull/123
   ```
   *(Or via python directly: `python3 claude_review.py --pr https://github.com/owner/repo/pull/123`)*

3. **(Optional) Post directly to GitHub or run tests**:
   ```bash
   ./claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
   python3 -m unittest test_claude_review.py
   ```

---

## 🚀 Features & Specifications

- **CLI Tooling**: `claude-review` executable wrapper and `claude_review.py`.
- **GitHub Actions Workflow**: Auto-review incoming PRs using `.github/workflows/claude-pr-review.yml`.
- **Structured Markdown Output**:
  - 📋 **Summary of changes** (2–3 sentences)
  - ⚠️ **Identified risks & blast radius** (list)
  - 💡 **Improvement suggestions** (list)
  - 🎯 **Confidence score**: High / Medium / Low (with Security, Coverage, and Maintainability breakdown)

---

## 🧪 Verified Real-World Sample Outputs

Tested on live GitHub PRs with output captured in `samples/`:
1. [Deen-Bridge/dnb-backend#470 Sample Review](samples/sample_review_pr470.md) (and [local copy](sample_review_pr470.md))
2. [claude-builders-bounty/claude-builders-bounty#4451 Sample Review](samples/sample_review_pr4451.md) (and [local copy](sample_review_pr4451.md))

---

## 🧪 Running Unit Tests

```bash
python3 -m unittest test_claude_review.py -v
```
