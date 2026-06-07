# Claude PR Review Agent

Automated pull request review powered by Claude AI. Runs as a CLI tool or GitHub Action.

## Features

- **AI-powered code review**: Security, correctness, performance analysis
- **Structured output**: Summary, Risks, Suggestions, Test Coverage, Verdict
- **GitHub Action**: Auto-review on PR open/sync
- **CLI mode**: Review any public PR from terminal

## Usage

### CLI

```bash
export GITHUB_TOKEN="ghp_..."
export ANTHROPIC_API_KEY="sk-ant-..."

chmod +x claude-review
./claude-review https://github.com/owner/repo/pull/123
./claude-review https://github.com/owner/repo/pull/123 --output json
```

### GitHub Action

1. Add `ANTHROPIC_API_KEY` to repository secrets
2. The `.github/workflows/pr-review.yml` workflow auto-reviews every PR
3. Review comment is posted automatically

## Output Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CLAUDE CODE REVIEW — PR #123
  owner/repo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Summary
Brief overview of the PR changes and purpose.

## Risks
- 🔴 Security: Potential SQL injection in user query builder
- 🟡 Performance: N+1 query in user listing endpoint
- 🟢 Style: Minor formatting inconsistencies

## Suggestions
1. Use parameterized queries instead of string concatenation
2. Add database indexing for the new query pattern
3. Consider pagination for large result sets

## Test Coverage
- ✅ Unit tests for auth middleware
- ❌ Missing integration tests for database layer

## Verdict
🟡 **Changes Requested** — Address security concerns before merge
```
