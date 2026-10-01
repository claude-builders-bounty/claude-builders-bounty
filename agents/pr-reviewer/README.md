# Claude Code PR Review Sub-Agent (`claude-review`)

An intelligent sub-agent and GitHub Action that ingests PR diffs, conducts static and contextual code analysis, and posts structured Markdown review comments.

## 🌟 Key Features
- **Dual Execution Modes:** Runs seamlessly via interactive CLI or automated GitHub Actions workflow.
- **Structured Markdown Output:**
  - 📝 **Summary of Changes:** 2–3 concise sentences outlining modified files and primary intent.
  - ⚠️ **Identified Risks:** Heuristic detection of credentials, missing tests, destructive operations, or large blast radius.
  - 💡 **Improvement Suggestions:** Actionable feedback on lockfiles, backward compatibility, and typing.
  - 🎯 **Confidence Score:** High / Medium / Low score calibrated against the code's risk profile.

---

## 🚀 Usage

### 1. Interactive CLI Mode

Install or run directly:
```bash
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
```

Export directly to a file:
```bash
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

### 2. GitHub Actions Integration

Drop `.github/workflows/claude-review.yml` into your repository. It triggers automatically on new PRs and posts the analysis as an automated review comment.

---

## 🧪 Real-World Verification Samples

### Sample 1: Tested on PR #4599 (`claude-builders-bounty`)
```bash
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4599
```
*Output:*
> #### 📝 Summary of Changes
> This pull request updates **2 file(s)** with **+115 additions** and **-0 deletions**. The primary changes focus on feat(template): add opinionated Next.js 15 + SQLite CLAUDE.md template.
> #### ⚠️ Identified Risks
> - None identified. The changes appear modular, scoped, and well-contained.
> #### 💡 Improvement Suggestions
> - Ensure type checking and linting pass across all targets.
> - Verify backwards compatibility for external consumers or dependent APIs.
> #### 🎯 Confidence Score
> **High**

---

### Sample 2: Tested on PR #4626 (`claude-builders-bounty`)
```bash
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4626
```
*Output:*
> #### 📝 Summary of Changes
> This pull request updates **4 file(s)** with **+204 additions** and **-0 deletions**. The primary changes focus on feat(hook): add pre-tool-use security hook blocking destructive bash commands.
> #### ⚠️ Identified Risks
> - None identified. The changes appear modular, scoped, and well-contained.
> #### 💡 Improvement Suggestions
> - Ensure type checking and linting pass across all targets.
> #### 🎯 Confidence Score
> **High**
