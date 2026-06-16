# PR Reviewer

A Claude Code sub-agent that reviews pull requests and posts structured comments.

## Usage

```
/pr-review
```

Or with specific PR number:
```
/pr-review 42
```

## What it does

1. Fetches the PR diff (current branch vs main, or specific PR via gh CLI)
2. Analyzes the diff across 4 dimensions:
   - **Bugs**: logic errors, edge cases, race conditions
   - **Security**: injection risks, auth issues, exposed secrets
   - **Performance**: N+1 queries, unnecessary allocations, blocking operations
   - **Style**: naming, consistency, documentation, type safety
3. Posts findings as a structured PR comment with severity tags
4. Each finding includes: file reference, line numbers, explanation, suggested fix

## Output Format

```markdown
## 🔍 PR Review — [branch/PR name]

### 🚨 Critical
- **file:line** — Description of the issue
  Suggested fix: ...

### ⚠️ Warnings
- **file:line** — Description
  Suggested fix: ...

### 💡 Suggestions
- **file:line** — Description
  Suggested fix: ...

### ✅ What's Good
- Positive observations

---
🤖 Reviewed by Claude Code PR Reviewer
```

## Instructions

1. Get the diff: `git diff origin/main...HEAD` or `gh pr diff <number>`
2. Scan for common bug patterns (null checks, error handling, race conditions)
3. Check for security issues (injection, auth, secrets)
4. Look for performance anti-patterns
5. Review style consistency with surrounding code
6. Generate structured comment
7. Post via `gh pr comment <number> --body-file review.md`
8. Co-author: `Co-Authored-By: Claude <noreply@anthropic.com>`
