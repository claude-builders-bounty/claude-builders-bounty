---
name: pr-reviewer
description: Automated PR reviewer agent that analyzes git diffs for security vulnerabilities, code quality issues, test coverage, and documentation, producing structured Markdown review reports with recommendations and actionable patches.
---

# PR Reviewer Agent (`/review-pr`)

Automated PR reviewer skill for Claude Code that analyzes unified diffs and outputs structured, deterministic Markdown code reviews.

## Capabilities

1. **Security & Vulnerability Analysis**:
   - Detects hardcoded secrets, API keys, private keys, and passwords.
   - Flags SQL injection risks from unparameterized queries, f-strings, and string concatenations.
   - Detects insecure shell execution (`os.system`, `subprocess(shell=True)`, `eval`, `exec`).
   - Identifies path traversal risks with unvalidated user input in file paths.

2. **Code Quality & Regressions**:
   - Identifies unhandled exceptions, bare `except:`, and silent error swallowing (`except Exception: pass`).
   - Detects missing null/existence checks on payload dictionary lookups.
   - Flags excessive cyclomatic complexity and deep nesting.

3. **Test Coverage & Documentation**:
   - Verifies whether new non-test code includes accompanying unit test additions or updates.
   - Checks if significant changes include updated documentation or docstrings.

4. **Structured Markdown Output**:
   - Clear recommendation badge: `APPROVE`, `REQUEST_CHANGES`, or `COMMENT`.
   - Confidence Score (1/5 to 5/5).
   - Executive Summary metric table.
   - Detailed Findings table with Severity, Category, File, Line, and Description.
   - Actionable Suggestions and Code Patches.

---

## Usage

### Slash Command

```bash
/review-pr [diff_file_or_branch]
```

### CLI Execution

```bash
# Review a diff file
python3 scripts/pr_reviewer.py path/to/changes.diff

# Review active git diff against main
git diff origin/main...HEAD | python3 scripts/pr_reviewer.py

# Review staged changes
git diff --cached | python3 scripts/pr_reviewer.py

# Pass diff file via flag and write output to file
python3 scripts/pr_reviewer.py --diff pr_patch.diff -o review_report.md

# Enforce strict CI mode (exits with code 1 on REQUEST_CHANGES)
python3 scripts/pr_reviewer.py --strict changes.diff
```

---

## Output Example

```markdown
# Pull Request Review Report

**Recommendation:** `APPROVE`  
**Confidence Score:** 5/5

---

## Executive Summary

| Metric | Value |
| :--- | :--- |
| **Files Changed** | 2 |
| **Lines Added** | +45 |
| **Lines Removed** | -10 |
| **Critical Vulnerabilities** | 0 |
| **Warnings / Issues** | 0 |
| **Info / Suggestions** | 0 |
| **Test Coverage Status** | Added / Updated |
| **Documentation Status** | Updated |
| **Overall Decision** | `APPROVE` |

## Detailed Findings

No critical issues, security vulnerabilities, or regressions detected. Code is clean.
```
