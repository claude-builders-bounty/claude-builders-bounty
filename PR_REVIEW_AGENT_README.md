# Claude Code PR Review Agent

A CLI tool that uses Claude to generate structured code reviews for GitHub Pull Requests.

## Setup

1. Ensure `gh` CLI is authenticated (`gh auth login`)
2. Ensure Claude CLI is configured with GhostCLI provider
3. Copy `claude-review.sh` to your PATH or project directory
4. Make executable: `chmod +x claude-review.sh`

## Usage

```bash
# Review a PR and print to stdout
./claude-review.sh --pr https://github.com/owner/repo/pull/123

# Save review to file
./claude-review.sh --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output Format

The agent produces structured Markdown with:
- **Summary**: 2-3 sentence overview of changes
- **Risks**: Identified potential issues or concerns
- **Suggestions**: Actionable improvement recommendations  
- **Confidence**: Low/Medium/High assessment with reasoning

## Sample Outputs

### Example 1: Feature Addition PR
```markdown
## Summary
This PR adds user authentication middleware using JWT tokens. It includes token validation, expiration handling, and error responses for unauthorized access.

## Risks
- Token secret is hardcoded; should use environment variable
- No rate limiting on auth endpoints could enable brute force attacks
- Missing input validation on token format before parsing

## Suggestions
- Move JWT_SECRET to environment configuration
- Add rate limiting middleware to auth routes
- Validate token structure before attempting verification
- Consider adding refresh token mechanism for better UX

## Confidence
High — Well-defined scope with clear security patterns to evaluate
```

### Example 2: Bug Fix PR
```markdown
## Summary
Fixes race condition in database connection pool by adding mutex locking around connection acquisition. Includes timeout handling to prevent deadlocks.

## Risks
- Mutex contention could impact performance under high load
- Timeout value (30s) may be too long for latency-sensitive operations

## Suggestions
- Consider using channel-based connection pooling instead of mutex
- Make timeout configurable via environment variable
- Add metrics to track connection wait times

## Confidence
Medium — Concurrency fixes are correct but performance implications need testing
```

## Requirements

- Bash 4+
- GitHub CLI (`gh`) authenticated
- Claude CLI with GhostCLI provider configured
- Internet connection for API calls
