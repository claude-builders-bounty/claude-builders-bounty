⬛ **CORTEX Code Review (Claude 3.5)**

This PR introduces a new rate-limiting middleware to the Express server using Redis. The logic is functionally sound for positive flows but lacks critical fallback mechanisms in transient failure states.

### Observations:
- `src/middleware/rateLimiter.js:L42`: If the Redis connection drops, `client.get(ip)` will throw an unhandled exception, causing subsequent requests to hit a 500 status rather than failing open or gracefully handling the missing cache.
- `src/middleware/rateLimiter.js:L55`: The TTL for the cache key is set synchronously. Consider wrapping this in an atomic `MULTI` query (or `set(..., 'EX', ...)` directly) to avoid race conditions and ghost keys if the process crashes mid-execution.

### Verdict:
[REQUEST CHANGES]
Please wrap the Redis calls in a `try/catch` and decide whether to "fail open" (allow traffic if Redis drops) or fail closed, logging the circuit breaker state. Also, consolidate the increment and expire steps into an atomic transaction.
