# PR Review Agent — Claude Code Sub-Agent

Analyzes GitHub PR diffs and returns structured Markdown review comments.

## CLI Usage

```bash
# Basic usage
python pr_review.py --pr https://github.com/owner/repo/pull/123

# Shorthand
python pr_review.py --pr owner/repo/123

# Save to file
python pr_review.py --pr owner/repo/123 --output review.md
```

## Output Format

```markdown
## PR Review

**Title:** Fix login redirect loop

### Summary
Changes 15 additions, 3 deletions across 2 files.
Primary files: src/auth/login.ts, src/middleware.ts

### Identified Risks
- [CRITICAL] Possible secret exposure in `src/auth/login.ts`
- [MEDIUM] TODO/FIXME found in `src/middleware.ts`

### Improvement Suggestions
- Consider adding error boundary for auth failures
- Add test coverage for redirect edge cases

### Stats
| Metric | Value |
|--------|-------|
| Files Changed | 2 |
| Additions | 15 |
| Deletions | 3 |
| Confidence | **High** |
```

## GitHub Action

Also available as a GitHub Action — included `.github/workflows/pr-review.yml`.

Trigger by commenting `/opere try` on any issue/PR.

## Requirements

- Python 3.10+
- GitHub token in `GITHUB_TOKEN` environment variable (for private repos)

## Detection Capabilities

- Secrets & credentials (API keys, tokens, passwords)
- Security weaknesses (eval, innerHTML, SQL injection)
- Code quality issues (TODO/FIXME, debug logging, HTTP URLs)
- Hardcoded values (passwords, localhost, connection strings)
- PR structure (size, scope, file count)
