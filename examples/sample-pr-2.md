## Claude Review

### Summary
- This PR updates 2 file(s): app/api/sessions.ts, prisma/schema.prisma.
- The diff contains 44 added line(s) and 9 removed line(s), so the main review focus should be behavior changes and regression coverage around the touched paths.

### Identified Risks
- Touches authentication, tokens, or secrets; confirm no sensitive values are logged or exposed.
- Changes persistence or schema-related code; check migration and rollback behavior.

### Improvement Suggestions
- Add or update automated tests for the changed behavior.
- Include the exact local verification commands and results in the PR description.

### Confidence
High
