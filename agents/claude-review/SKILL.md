---
name: claude-review
description: Analyze a GitHub PR diff and produce a structured code review with Summary, Risks, Suggestions, and Confidence score. Use when asked to review a PR, when given a PR URL/number, or when the user asks for a code review.
---

# claude-review Agent

Analyzes GitHub PRs and produces structured code review comments.

## Usage

```
/claude-review https://github.com/owner/repo/pull/123
/claude-review owner/repo#123
```

## Workflow

1. **Fetch PR data** using the GitHub CLI:
   ```bash
   gh pr view <pr_num> --repo <owner>/<repo> --json title,body,files,additions,deletions,author,comments
   gh diff <pr_num> --repo <owner>/<repo>
   ```

2. **Analyze the diff** considering:
   - Security vulnerabilities (SQL injection, XSS, auth bypass, reentrancy, etc.)
   - Correctness issues (logic errors, race conditions, edge cases, off-by-one)
   - Code quality (naming, structure, duplication, complexity)
   - Test coverage (are new code paths tested? are edge cases covered?)
   - Performance implications (N+1 queries, unnecessary allocations, missing indexes)
   - Breaking changes (API changes, schema migrations, backward compatibility)

3. **Output structured review** in this exact format:

```markdown
## Summary
[2-3 sentence summary of what this PR does and its approach]

## Risks
- **[HIGH/MEDIUM/LOW] Risk title**: Description of the risk and its potential impact
  - File: `path/to/file.ts:line`
  - Recommendation: How to mitigate

## Suggestions
- **Suggestion title**: Specific actionable improvement
  - File: `path/to/file.ts:line`
  - Example: Code snippet if applicable

## Confidence: XX/100
[Brief justification for the confidence score]
```

## Severity Levels
- **HIGH**: Security vulnerability, data loss risk, crash in production, funds at risk
- **MEDIUM**: Logic error, performance issue, maintainability concern, missing validation
- **LOW**: Style issue, minor improvement, nice-to-have, documentation gap

## Confidence Score Guide
- 90-100: Trivial change (docs, typo fix), well-tested, no risks identified
- 70-89: Straightforward change, minor risks, good test coverage
- 50-69: Moderate complexity, some risks identified, needs careful review
- 30-49: Complex change, significant risks, needs thorough testing
- 0-29: Major refactor, high risk, needs extensive review and testing

## Posting Reviews

After generating the review, post it as a comment on the PR:

```bash
gh pr comment <pr_num> --repo <owner>/<repo> --body "<review content>"
```

Include the wallet address for bounty claims when applicable:
```
Wallet for bounty: 0xd9c96DF15CF857E31ee3A4ABD6315233288a8A2F
```

## Review Checklist

When reviewing, always check:
- [ ] Input validation on all user-provided data
- [ ] Error handling (no silent failures)
- [ ] SQL injection prevention (parameterized queries)
- [ ] Authentication and authorization checks
- [ ] Race conditions in concurrent code
- [ ] Resource cleanup (file handles, DB connections)
- [ ] Logging of security-relevant events
- [ ] Test coverage for new code paths
- [ ] Backward compatibility
- [ ] Documentation updates for API changes
