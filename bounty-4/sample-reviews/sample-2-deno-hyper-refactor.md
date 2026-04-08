## PR Review: denoland/deno#24000 — Refactor HTTP client to use hyper 1.0

### Summary
This PR migrates Deno's internal HTTP client from hyper 0.14 to hyper 1.0, bringing improved performance and streaming support. It touches the core `fetch()` implementation, HTTP cache, and proxy handling.

### Risks
- **High** — Large refactor affecting all HTTP operations; regression risk is significant.
- **Medium** — Proxy authentication flow has changed; manual testing needed for NTLM/Kerberos.
- **Low** — Some internal APIs renamed; downstream consumers may need updates.

### Suggestions
1. Add a migration guide for code depending on `Deno.HttpClient` internals.
2. Increase integration test coverage for chunked transfer encoding edge cases.
3. Verify WebSocket upgrade behavior remains unchanged under hyper 1.0.
4. Add a benchmark comparison table in the PR description.

### Confidence
**Medium** — Large scope with many interdependent changes; some edge cases may surface post-merge.
