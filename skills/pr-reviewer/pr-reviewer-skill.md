---
name: pr-reviewer
description: "Review pull requests and produce structured Markdown output with code quality assessment, security concerns, test coverage check, and suggested improvements."
---

# PR Reviewer Agent

## Purpose

Automatically review pull requests and generate comprehensive, structured Markdown reports covering code quality, security, testing, documentation, and improvement suggestions.

## Workflow

1. **Fetch PR details.**
   - Use GitHub API or `gh pr view <number>` to get PR metadata.
   - Fetch diff: `gh pr diff <number>` or GitHub API `/pulls/<number>/files`.
   - Get conversation: `gh pr view <number> --comments`.
   - **Done when:** you have PR title, description, files changed, and discussion context.

2. **Analyze code changes.**
   - Treat the unified patch as authoritative for paths and added/deleted line counts; metadata is context only.
   - Categorize paths as code, tests, documentation/examples, generated/vendor, or deletion-heavy changes.
   - Inspect attributable added non-documentation lines for high-confidence risks such as hardcoded credentials, dynamic execution, and shell injection. Documentation examples are reported as uncertainty/notes, not code findings.
   - **Done when:** the patch parses completely, every finding has an exact changed path and line excerpt, and uncertainty is explicit.

3. **Assess code quality.**
   - Check naming conventions, function length, complexity.
   - Verify consistent style (indentation, braces, imports).
   - Look for duplicated code or overly complex logic.
   - **Done when:** quality score assigned with specific examples.

4. **Check security concerns.**
   - Scan for: SQL injection, XSS, command injection, hardcoded credentials, insecure dependencies.
   - Verify input validation on user-facing endpoints.
   - Check authentication/authorization changes.
   - **Done when:** all security risks identified or confirmed absent.

5. **Verify test coverage.**
   - Check if new code has corresponding tests.
   - Verify existing tests still pass (if CI available).
   - Note untested edge cases.
   - **Done when:** test gap analysis complete.

6. **Review documentation.**
   - Check if public APIs have docstrings/JSDoc.
   - Verify README/changelog updated if needed.
   - Confirm inline comments for complex logic.
   - **Done when:** documentation completeness assessed.

7. **Generate structured report.**
   - Output Markdown with sections: Summary, Code Quality, Security, Tests, Documentation, Suggestions, and Confidence.
   - Include exact diff evidence, specific changed-path excerpts for findings, and metadata mismatches as uncertainty.
   - Empty, trivial, malformed, inaccessible, and binary-only input must receive an explicit no-review result, not a generic count summary.
   - Optionally bind audit artifacts with candidate SHA, worktree, clean state, evidence SHA, and audit SHA; never infer those values.
   - **Done when:** report is complete, conservative, and ready for review (posting remains opt-in).

## Example Output

```markdown
## PR Review Report

### 📋 Summary
- **PR:** #42 — Add user authentication
- **Files changed:** 8 (342 lines added, 45 removed)
- **Overall assessment:** ⚠️ Needs revision before merge

### ✅ Code Quality
- Consistent TypeScript usage across new files
- Good separation of concerns in auth module
- ⚠️ Function `validateToken` is 80 lines — consider splitting

### 🔒 Security
- ✅ No hardcoded credentials detected
- ⚠️ JWT secret loaded from env but no fallback validation
- ❌ Missing rate limiting on login endpoint

### 🧪 Tests
- ✅ New unit tests for auth service (8 tests)
- ❌ No integration tests for login flow
- ⚠️ Edge case: expired token refresh not tested

### 📖 Documentation
- ✅ JSDoc added for all public functions
- ❌ README not updated with new auth endpoints
- ⚠️ Changelog entry missing

### 💡 Suggestions
1. Add rate limiting middleware to `/api/login`
2. Split `validateToken` into smaller functions
3. Add integration test for full login → protected route flow
4. Update README with auth endpoint documentation
```

## Installation

Save as an OpenClaw skill or Claude Code hook. Trigger manually on PR review requests or automate via webhook.

## Notes

- For large PRs (>500 lines), focus on high-risk areas first.
- Use deterministic checks where possible (linting, static analysis).
- LLM judgment reserved for subjective quality/style assessments.
- Never approve PRs automatically — always require human confirmation.
