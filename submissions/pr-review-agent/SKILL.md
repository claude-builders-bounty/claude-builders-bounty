---
name: claude-review
description: Use when the user asks Claude to review a PR. Trigger: "review PR", "claude-review --pr URL", "review this pull request". Analyzes GitHub PR diffs for security, logic, style issues.
---

# Claude PR Review Agent

A Claude Code sub-agent that takes a GitHub PR URL, analyzes the diff, and returns a structured review.

## Usage

```bash
python3 scripts/review-pr.py --pr https://github.com/owner/repo/pull/123
```

Or with a GitHub token for posting comments:
```bash
export GITHUB_TOKEN=ghp_xxx
python3 scripts/review-pr.py --pr https://github.com/owner/repo/pull/123 --post
```

## Behavior

1. Parses the PR URL to extract owner/repo/number
2. Fetches PR metadata + diff via GitHub API
3. Analyzes:
   - **Security**: hardcoded secrets, SQL injection patterns, XSS vectors, path traversal, unsafe eval/exec
   - **Logic**: missing error handling, race conditions, null/undefined access, incorrect assumptions
   - **Style**: inconsistent naming, missing types, overly complex functions
   - **Testing**: untested edge cases, missing test coverage for new code
4. Generates structured Markdown review
5. Optionally posts review comment on the PR

## Output Format

```markdown
## PR Review Summary
**PR**: #123 — feat: add user authentication
**Confidence**: High

### Summary
2-3 sentence overview of what changed and impact.

### Risks
- [HIGH] SQL injection in query builder (line 45)
- [MEDIUM] Missing rate limiting on login endpoint

### Suggestions
- Add input sanitization for `user_id` parameter
- Extract validation logic into middleware
- Add integration tests for auth flow

### Confidence: High | Medium | Low
Based on: diff completeness, code clarity, domain familiarity
```

## Setup

```bash
chmod +x scripts/review-pr.py
pip install requests  # if not already installed
```
