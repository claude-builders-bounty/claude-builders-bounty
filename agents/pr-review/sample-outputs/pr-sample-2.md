## 🤖 PR Review

### Summary
This PR adds a new `/api/v2/users` REST endpoint with pagination, filtering, and sorting capabilities to the Python FastAPI backend. It also introduces Pydantic v2 models for request/response validation and adds a Redis-based caching layer for frequently queried user profiles. The implementation spans 8 new files and modifies 3 existing ones.

### ⚠️ Risks
- The Redis cache has no TTL (time-to-live) configured, which means stale user data could be served indefinitely until manually invalidated.
- The `sort_by` query parameter is passed directly to an SQLAlchemy `order_by` call without an allowlist, creating a potential SQL injection vector via column name manipulation.
- The pagination `offset` parameter accepts negative values, which could cause unexpected query behavior.
- The `/api/v2/users/<id>` endpoint does not verify that the requesting user has permission to view the requested user's profile data.

### 💡 Suggestions
- Add a `CACHE_TTL` environment variable (default: 300 seconds) and pass it to the Redis `setex` call to prevent stale data accumulation.
- Validate the `sort_by` parameter against an explicit allowlist of sortable columns (e.g., `ALLOWED_SORT_FIELDS = {"name", "email", "created_at"}`) before passing it to the ORM query.
- Add a `min(0, offset)` guard or raise a 422 validation error for negative offset values.
- Add an authorization check in the single-user endpoint to ensure the requester has appropriate access rights.
- Consider adding rate limiting on the list endpoint to prevent abuse of the filtering/sorting features.

### Confidence: **High**

The PR is well-organized with clear separation of concerns. The Pydantic models and FastAPI router structure follow best practices. The identified risks are straightforward to address and the overall approach is sound.
