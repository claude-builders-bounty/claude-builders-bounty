# 🔍 claude-review — AI-Powered PR Review Agent

A Claude Code agent that takes a PR URL, analyzes the diff, and returns a structured Markdown review comment.

## Setup & Usage

### CLI Mode

```bash
# 1. Install dependencies (gh CLI + Anthropic API key)
# gh CLI: https://cli.github.com
export ANTHROPIC_API_KEY=sk-ant-your-key

# 2. Run the review
./claude-review --pr https://github.com/owner/repo/pull/123
```

### GitHub Action Mode

```bash
# 1. Copy .github/workflows/pr-review.yml to your repo

# 2. Add secret: ANTHROPIC_API_KEY
# Settings → Secrets → Actions → New repository secret

# 3. Open a PR — review comment posts automatically
```

## Output Format

Every review includes:

### Summary
2-3 sentences describing what the PR does.

### Identified Risks
Specific risks across categories:
- **Security**: SQL injection, XSS, auth bypass, exposed secrets
- **Performance**: N+1 queries, unbounded loops, memory leaks
- **Correctness**: Logic errors, race conditions, off-by-one
- **Maintainability**: Code duplication, unclear naming, missing tests

### Improvement Suggestions
Actionable improvements with code examples where helpful.

### Confidence Score
- **Low**: Large PR, many files, insufficient context
- **Medium**: Moderate size, some domain knowledge needed
- **High**: Small, focused PR with clear intent

## Sample Outputs

### Sample 1: Small Bug Fix PR

```
═══════════════════════════════════════════
  PR Review: #42 — acme/webapp
═══════════════════════════════════════════

## Summary
This PR fixes a null pointer exception in the user authentication flow by adding a null check before accessing the user's session object. It also includes a test case for the edge case.

## Identified Risks
- The null check only covers `user.session` but not `user.session.token`, which could still throw if session exists but token is null
- The error message leaks internal state ("Session token is null") which could aid attackers

## Improvement Suggestions
- Add a deeper null check: `if (user?.session?.token)` using optional chaining
- Return a generic error message: "Authentication failed" instead of exposing null token
- Consider using a typed `Result` instead of throwing exceptions for expected failures

## Confidence: High
Small, focused PR with clear intent and test coverage. The fix is correct but could be more defensive.
```

### Sample 2: Feature Addition PR

```
═══════════════════════════════════════════
  PR Review: #107 — acme/api-service
═══════════════════════════════════════════

## Summary
This PR adds a new /api/v2/search endpoint with pagination, filtering, and caching. It modifies 12 files across the API, service, and repository layers, adding approximately 400 lines of new code.

## Identified Risks
- **Security**: The filter parameter is interpolated directly into the SQL query (line 47 of SearchRepository.java) — potential SQL injection
- **Performance**: The cache has no TTL or eviction policy; under high load, it will grow unbounded and cause OOM
- **Correctness**: The pagination offset is not validated — negative offsets will cause unexpected behavior
- **Breaking change**: The response format differs from /api/v1/search — existing clients may break

## Improvement Suggestions
- Use parameterized queries instead of string interpolation for the filter clause:
  ```java
  // Instead of:
  String sql = "SELECT * FROM items WHERE " + filter;
  // Use:
  PreparedStatement stmt = conn.prepareStatement("SELECT * FROM items WHERE name LIKE ?");
  stmt.setString(1, "%" + filter + "%");
  ```
- Add cache eviction: `CacheBuilder.newBuilder().maximumSize(1000).expireAfterWrite(10, TimeUnit.MINUTES)`
- Validate pagination: `if (offset < 0) throw new IllegalArgumentException("offset must be >= 0")`
- Add API versioning documentation and migration guide for v1→v2

## Confidence: Medium
The PR is moderately large (12 files). The SQL injection risk is clear, but there may be context I'm missing about the filter sanitization happening upstream. The caching concern is straightforward.
```

## Post Review as Comment

```bash
# Auto-post review as PR comment
export POST_COMMENT=true
export GITHUB_TOKEN=ghp_your_token
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Requirements

- `gh` CLI (authenticated)
- Anthropic API key OR Claude CLI
- Python 3.7+ (for JSON parsing)
