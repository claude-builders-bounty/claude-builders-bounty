# Claude Code PR Reviewer Agent

A Python agent that fetches a PR diff, analyzes it, and outputs a structured Markdown review.

## Features

- Fetches PR diff via GitHub API
- Detects security risks (SQL injection, hardcoded secrets, eval/exec, XSS)
- Identifies code quality issues (debug statements, TODOs, empty catch blocks)
- Outputs structured Markdown: Summary → Risks → Suggestions → Confidence
- Optionally posts the review as a PR comment

## Installation (2 steps)

```bash
# 1. Install (no dependencies needed — uses Python stdlib)
chmod +x claude-review.py

# 2. Set your GitHub token (for private repos and posting comments)
export GITHUB_TOKEN=ghp_your_token_here
```

## Usage

```bash
# Review a PR (prints to stdout)
python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# Save review to file
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md

# Post review as a PR comment
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --post
```

## Sample Output

```markdown
## PR Review: Add OAuth2 login flow

**Author:** jsmith
**Branch:** main ← feature/oauth
**Files changed:** 5
**+127/-23**

### Summary
This PR adds 5 file(s) (+127/-23) across 3 commit(s). The changes: "Add OAuth2 login flow".

### Files Changed
- `src/lib/auth.ts`
- `src/app/(auth)/login/page.tsx`
- `src/app/api/auth/callback/route.ts`

### Identified Risks
- `src/lib/auth.ts`: Hardcoded credential detected
- `src/app/api/auth/callback/route.ts`: Use of `eval`/`exec` — potential code injection risk

### Improvement Suggestions
- `src/lib/auth.ts`: Remove debug statements (console.log/print)

### Confidence Score
**Low**

> Low confidence due to large diff size. Manual review recommended.
```

## Risk Detection

| Category | Patterns Detected |
|----------|-------------------|
| SQL Injection | String concatenation in queries |
| Hardcoded Secrets | password/secret/api_key = "value" |
| Code Injection | eval(), exec() calls |
| XSS | innerHTML usage |
| Silent Errors | Empty catch/except blocks |
| Debug Code | console.log, print() |
| Tech Debt | TODO, FIXME, HACK markers |
| Irreversible Ops | DROP TABLE/DATABASE in SQL |

## Confidence Scoring

| Score | Condition |
|-------|-----------|
| High | < 50 lines changed AND no risks |
| Medium | 50-500 lines changed |
| Low | > 500 lines changed OR complex changes |
