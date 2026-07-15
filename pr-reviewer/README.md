# PR Reviewer Agent

Automated PR review with structured Markdown output.

## Quick Setup (2 Steps)

1. **Copy** `pr-reviewer/` to your project or install globally
2. **Run** `python pr-reviewer/pr_reviewer.py`

## Features

- 🔍 Automatic code review from git diff
- 📝 Structured Markdown output
- 🐛 Security, bug risk, performance, and style checks
- 📊 Summary statistics with severity levels
- 🔧 JSON output option for CI/CD integration

## Usage

```bash
# Review current branch against main
python pr_reviewer.py

# Review against specific branch
python pr_reviewer.py --base develop

# Save to file
python pr_reviewer.py --base main --o review-report.md

# JSON output
python pr_reviewer.py --json
```

## Checks Performed

| Category | Checks |
|----------|--------|
| 🔒 Security | Hardcoded secrets, SQL injection risks |
| 🐛 Bug Risk | TODO/FIXME without refs, bare except clauses |
| ⚡ Performance | Inefficient loops |
| 🎨 Style | Trailing whitespace, long lines |

## Output Example

```markdown
# 🔍 PR Review Report

**PR:** Review: feature-branch
**Branch:** `feature-branch` → `main`
**Author:** John Doe

## 📊 Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | 1 |
| 🟡 Medium | 2 |

## 📝 Findings

### 🔴 CRITICAL

**🔒 Security** in `config.py:42`

- **Issue:** Hardcoded password detected
- **Suggestion:** Use environment variables or a secrets manager
```

## Bounty

Part of [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) #4 ($150)
