### Summary of changes
This PR refactors the `fetch_user_analytics` function to use a single SQL JOIN query instead of performing multiple N+1 database calls within a loop. It also updates the data models to include a new `last_login` timestamp and modifies the corresponding API endpoint to serialize this new field.

### Identified risks
*   **Performance / Lock Contention:** The new JOIN query spans across three large tables (`users`, `events`, and `transactions`) without a `LIMIT` clause, which could cause full table scans and lock contention in production.
*   **Security:** The SQL query uses string formatting (`f"SELECT ... {user_id}"`) rather than parameterized queries, leaving the application vulnerable to SQL injection.
*   **Data Integrity:** The `last_login` field defaults to `NULL` for existing users in the migration, which could cause `AttributeError` exceptions in the downstream serialization logic if not properly handled.

### Improvement suggestions
*   Rewrite the SQL query to use parameterized inputs (e.g., `execute("... WHERE id = %s", (user_id,))`) to prevent SQL injection.
*   Add a `LIMIT` and `OFFSET` clause for pagination, or restrict the query by a specific date range, to avoid fetching millions of rows at once.
*   Update the database migration to set a default value for `last_login` (e.g., `CURRENT_TIMESTAMP`) or handle the `None` case explicitly in the Pydantic model.

### Confidence score
Medium. The intent to remove the N+1 query issue is correct, but the implementation introduces severe SQL injection risks and scalability problems that must be fixed before merging.
