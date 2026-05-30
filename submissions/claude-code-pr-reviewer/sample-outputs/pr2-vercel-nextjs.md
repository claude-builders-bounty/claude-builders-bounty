# PR Review: feat: add `generateStaticParams` caching layer

**Repo:** vercel/next.js  
**PR:** https://github.com/vercel/next.js/pull/69102

---

## Summary of Changes
This PR introduces an in-memory caching layer for `generateStaticParams` results to avoid redundant computation during incremental static regeneration (ISR). When multiple requests trigger the same static path generation within a 60-second window, the cached result is returned instead of re-executing the async function.

## Identified Risks
- **Stale data**: The 60-second TTL is hardcoded; teams regenerating content frequently may serve stale params
- **Memory bloat**: Projects with thousands of dynamic routes (e.g., `/products/[id]`) could accumulate significant cache entries under heavy load
- **No cache invalidation on deploy**: Cache persists across hot reloads in dev mode but is not invalidated when the `generateStaticParams` implementation changes

## Improvement Suggestions
- Make the TTL configurable via `next.config.js` (`experimental.staticParamsCacheTTL`)
- Implement a maximum cache size with LRU eviction to prevent unbounded memory growth
- Add `cache: 'no-store'` support per-route to allow opt-out for frequently-changing content

## Confidence Score
**High**

---

*Reviewed by claude-review v1.0.0*
