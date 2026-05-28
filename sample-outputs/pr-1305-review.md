## PR Review: Add budgetMin <= budgetMax validation to job creation schema (#1304)

**Repo:** SecureBananaLabs/bug-bounty | **PR:** #1305

### Summary
This PR adds input validation to the job creation endpoint ensuring that `budgetMin` does not exceed `budgetMax`. It introduces a Joi/Zod schema validation layer to enforce this business rule before data reaches the database.

### Identified Risks
- Validation logic is in the controller layer but there is no server-side database constraint; a race condition or bypass could still insert invalid data
- The error message returned to the client exposes the internal validation rule, which could aid attackers in understanding the schema
- No negative test cases (e.g., budgetMin > budgetMax) are covered

### Improvement Suggestions
- Add a database-level CHECK constraint as a defense-in-depth measure
- Move validation to a middleware layer for reuse across create/update endpoints
- Add test cases for both valid and invalid budget combinations

### Confidence Score
**Confidence: Medium**
The change is functionally correct and addresses the reported issue, but lacks defense-in-depth and full test coverage. The validation could be more robust with database constraints.
