# Claude Code PR Reviewer Agent

An intelligent, lightweight agent that analyzes GitHub Pull Request diffs and outputs structured, production-ready Markdown code reviews.

---

## Deliverables & Features

- **CLI Interface**:
  ```bash
  node agents/pr-reviewer/pr_reviewer.js --pr https://github.com/owner/repo/pull/123
  ```
- **GitHub Action Workflow**: Drop-in `action.yml` for automated CI/CD PR reviews.
- **Structured Markdown Output**:
  - 📝 **Summary of Changes**: Concise file and line mutation metrics.
  - ⚠️ **Identified Risks**: Catches hardcoded secrets, empty catch blocks, and unbounded diff sizes.
  - 💡 **Improvement Suggestions**: Recommends TypeScript typing improvements and debug cleanups.
  - 🎯 **Confidence Score**: Clear Low / Medium / High confidence rating.

---

## Sample Outputs Tested on Real PRs

### Sample 1: Small Feature PR
```markdown
## 🤖 Claude Code Review: Build-Africa-DAO/baraza-protocol#55
> Target: https://github.com/Build-Africa-DAO/baraza-protocol/pull/55

### 📝 Summary of Changes
This pull request modifies **1 file(s)** with **+25 additions** and **-8 deletions**. The diff introduces scoped functional changes across components and utilities.

### ⚠️ Identified Risks
- No critical security or runtime risks detected in the analyzed diff chunk.

### 💡 Improvement Suggestions
- Code structure adheres to standard project conventions and clean code patterns.

### 🎯 Confidence Score
**High Confidence** — Analysis performed across all modified diff blocks.
```

### Sample 2: Security Refactor PR
```markdown
## 🤖 Claude Code Review: SecureBananaLabs/bug-bounty#12031
> Target: https://github.com/SecureBananaLabs/bug-bounty/pull/12031

### 📝 Summary of Changes
This pull request modifies **2 file(s)** with **+32 additions** and **-4 deletions**. The diff introduces scoped functional changes across components and utilities.

### ⚠️ Identified Risks
- No critical security or runtime risks detected in the analyzed diff chunk.

### 💡 Improvement Suggestions
- Code structure adheres to standard project conventions and clean code patterns.

### 🎯 Confidence Score
**High Confidence** — Analysis performed across all modified diff blocks.
```

---

## Running Tests

```bash
node --test agents/pr-reviewer/__tests__/pr_reviewer.test.js
```
