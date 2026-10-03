## Summary
This PR refactors the authentication module to use OAuth 2.0 token refresh flow instead of the legacy session-based approach. It introduces a new `TokenManager` class, updates the API client middleware, and deprecates the old session handler with backward-compatible fallbacks.

## Identified Risks
- The token refresh logic may introduce a race condition if multiple requests fire simultaneously before the new token is cached
- Backward-compatible fallbacks add complexity and should be removed in the next major version
- No integration tests cover the refresh-flow edge case when the refresh endpoint returns 401

## Improvement Suggestions
- Add exponential backoff with jitter to the token retry logic
- Extract the refresh endpoint logic into a dedicated service for better testability
- Add a unit test for the concurrent-request race condition scenario
- Include a deprecation warning log when the legacy session handler is triggered

## Confidence Score
High
