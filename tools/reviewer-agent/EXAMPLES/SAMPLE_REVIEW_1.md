### PR Review: feat: optimize database indexing for large datasets

**Summary of changes**
This PR introduces composite indexes on the `events` and `logs` tables to improve query performance for historical data lookups. It also updates the migration scripts to handle concurrent index creation in PostgreSQL.

**Identified risks**
- Index creation on massive tables may cause temporary write locks if not executed with `CONCURRENTLY`.
- Increased storage overhead for the new composite indexes.

**Improvement suggestions**
- Verify that the index order (timestamp, user_id) matches the most frequent query patterns.
- Add a cleanup script for the old, redundant single-column indexes.

**Confidence score: High**
