### Summary
This Pull Request updates the PostgreSQL database schema by adding an `is_active` boolean flag to the `users` table and creates a background cron script to automatically deactivate users who haven't logged in for 90 days.

### Identified Risks
- The migration script adds the new column with a default value, which could lock the `users` table for a significant amount of time on large production databases.
- The cron script iterates over users synchronously, which could cause memory issues if the dataset grows too large.

### Improvement Suggestions
- Add the column without a default value first, and backfill the `is_active` status in batches to prevent database locking.
- Use pagination or a cursor in the background script to process inactive users in chunks of 1,000 rather than loading them all into memory at once.

### Confidence Score
Medium
