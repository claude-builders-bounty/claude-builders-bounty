**Summary of changes**:
This PR implements a new `/api/users` endpoint in the backend and adds a corresponding React hook for data fetching. It also includes basic unit tests for the new endpoint.

**Identified risks**:
- The new API endpoint lacks rate limiting, which could lead to abuse.
- The React hook uses `useEffect` without proper cleanup, potentially causing memory leaks on component unmount.
- The database query is missing pagination and could return too much data for large tables.

**Improvement suggestions**:
- Wrap the database query in a paginated function using `LIMIT` and `OFFSET`.
- Implement a cleanup function in the `useEffect` hook.
- Add standard rate-limiting middleware to the new route.

**Confidence score**: Medium