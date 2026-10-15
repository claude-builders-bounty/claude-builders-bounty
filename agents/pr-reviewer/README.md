# Claude Code PR Reviewer Sub-Agent 🔍

An autonomous, production-ready Claude Code agent that inspects Pull Request diffs, identifies security risks and edge cases, and publishes structured Markdown reviews.

---

## 🚀 Features

- **CLI Interface**: Review any public or private GitHub PR via command-line:
  ```bash
  ./agents/pr-reviewer/bin/claude-review --pr https://github.com/owner/repo/pull/123
  ```
- **Claude Code Native Sub-Agent**: Configured at `.claude/agents/pr-reviewer.md` with YAML frontmatter.
- **GitHub Action Integration**: Reusable workflow in `.github/workflows/claude-pr-review.yml`.
- **Structured Review Output**:
  - 📝 **Summary of Changes** (2-3 sentences)
  - ⚠️ **Identified Risks** (security, regressions, data hazards)
  - 💡 **Improvement Suggestions** (clean code, architecture, testing)
  - 🎯 **Confidence Score** (High / Medium / Low with explicit justification)
- **Zero Heavy Dependencies**: Pure standard library Python 3.

---

## 📦 Setup & Usage

### 1. Local CLI Execution
```bash
# Analyze a PR and print Markdown review
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123

# Post the review directly as a comment on GitHub
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123 --token "$GITHUB_TOKEN" --post-comment
```

### 2. Run Automated Test Suite
```bash
python3 agents/pr-reviewer/tests/test_review.py
```

### 3. GitHub Action Setup
Copy `.github/workflows/claude-pr-review.yml` into your repository to automatically review every open Pull Request.
