## Summary
This PR refactors database query helpers to reduce repeated SQL and centralize pagination logic. It improves readability and reduces inconsistent query filters.

## Risks
- Shared helper changes may affect endpoints not covered by tests.
- Pagination defaults could alter existing client behavior.

## Improvement Suggestions
- Add endpoint-level snapshots for list APIs.
- Document any paging default changes in release notes.

## Confidence
High
