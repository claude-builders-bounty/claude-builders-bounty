# claude-review — Automated PR Review Agent

A Claude Code sub-agent that reviews GitHub pull requests and posts
structured Markdown comments with risks, suggestions, and confidence scoring.

## CLI Usage

```bash
# Basic usage
python claude-review.py --pr https://github.com/owner/repo/pull/123

# Save to file
python claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

## GitHub Action Usage

Copy `.github/workflows/pr-review.yml` to your repo and configure a
GitHub token with `pull_request: read` permission.

## Sample Output

```
## 🤖 Automated PR Review — #687

**Confidence:** High  |  **Score:** 🟡 Minor concerns

---

### 📋 Summary

**PR:** [BOUNTY #2] TEMPLATE: CLAUDE.md for Next.js + SQLite
**Branch:** `bounty-2-template` → `main`
**Changes:** 1 file, +188/-0 lines

### ⚠️ Risks

- 🧪 No test files detected but justifiable for a document-only change

### 💡 Improvement Suggestions

- ✅ No issues — clean, well-structured PR
```

## What It Checks

| Check | Description |
|-------|-------------|
| TODO/FIXME | Incomplete work markers |
| Debug prints | Leftover console.log / print() |
| Large diffs | Files with 200+ changed lines |
| Test coverage | Whether tests accompany changes |
| Security | SQL injection, hardcoded secrets, eval() |
| Documentation | New public APIs without docstrings |
| Confidence | High / Medium / Low based on scope |
