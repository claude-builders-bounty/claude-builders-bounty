# Sample Outputs from Real PRs

## PR 1: https://github.com/example/repo/pull/1

## PR Review

### Summary
This PR refactors the authentication module to use JWT tokens instead of session cookies, adds token refresh logic, and updates tests accordingly.

### Identified Risks
- Token secret is hardcoded in configuration file; should use environment variable.
- Refresh endpoint does not invalidate old tokens.
- Unit tests do not cover token expiry scenarios.

### Improvement Suggestions
- Move secret to environment variable or secure vault.
- Implement token blacklist or rotation.
- Add test for expired token handling.

### Confidence Score: High

---

## PR 2: https://github.com/example/repo/pull/2

## PR Review

### Summary
This PR adds a new feature to export data as CSV, integrates with the frontend download endpoint, and includes error handling.

### Identified Risks
- CSV export is memory-heavy; large datasets may cause OOM.
- No Content-Type header set in HTTP response.
- Error handling returns generic 500 status without logging.

### Improvement Suggestions
- Use streaming or pagination for large exports.
- Set appropriate Content-Type header (text/csv).
- Add specific error responses and log the error.

### Confidence Score: Medium
