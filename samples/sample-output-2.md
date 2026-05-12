# PR Review: Refactor database layer to use connection pooling

**Repository:** claude-builders-bounty/demo-repo
**PR:** #47
**URL:** https://github.com/claude-builders-bounty/demo-repo/pull/47
**Review generated:** Claude claude-sonnet-4-20250514

---

## Summary

This PR refactors the database layer to replace individual connections with a `psycopg2.pool.ThreadedConnectionPool`. It affects the ORM wrapper and all query helper modules. Connection lifecycle is now managed centrally, which should improve performance under concurrent load.

## Identified Risks

- **Pool size is hardcoded to 5** — under heavy load this could become a bottleneck; should be configurable via env var with a sane default
- **No connection health check** — stale connections in the pool are not validated before use; a `SELECT 1` test on checkout would prevent surprising failures
- **Connection leak on exception** — in the `db_query` helper, if the query raises after checkout, `putconn` is not called in the `except` path, which will exhaust the pool

## Improvement Suggestions

- Wrap the checkout/query/putconn cycle in a context manager for guaranteed cleanup
- Add `pool_max` and `pool_min` environment variables with sensible defaults (min=2, max=20)
- Include a retry mechanism for transient database errors
- Log pool stats (available, used) at debug level for monitoring

## Confidence Score

**High** — The approach is sound and the diff is clean. The two bugs (leak, hardcoded size) are easy to fix and important, but the overall direction is right.
