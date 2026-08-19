### Summary
This PR modifies the `fetch_data()` utility in `api_client.js` to include a timeout parameter and proper error handling. It replaces the previous silent-fail behavior with throwing an explicit `TimeoutError` when the server takes longer than 5000ms to respond.

### Identified Risks
- Breaking change: Any component calling `fetch_data()` without a `try/catch` block will now crash the application if a timeout occurs.
- The default 5000ms timeout might be too aggressive for users on slow mobile networks.

### Improvement Suggestions
- Wrap existing calls to `fetch_data()` across the codebase in `try/catch` to handle the new `TimeoutError` gracefully.
- Consider making the timeout value configurable via an environment variable or passing it in from the UI layer.

### Confidence Score
High
