## PR Review

### Summary of changes
This PR restores the navbar search control and wires it into the Items and Admin Users pages. It adds client-side filtering for loaded table data, including empty states when no rows match.
Source reviewed: `https://github.com/gitearn-io/gitearn/pull/30`.

### Changed files
- `frontend/src/components/Common/Navbar.tsx`
- `frontend/src/routes/_layout/items.tsx`
- `frontend/src/routes/_layout/admin.tsx`

### Identified risks
- Client-side filtering only covers records already loaded by the existing `readItems` and `readUsers` calls; if pagination grows later, search results may be incomplete.
- The Admin page filters role and status labels in English, so translated UI labels would need matching search behavior if localization is added.

### Improvement suggestions
- Add component or route tests for matching and empty-state behavior.
- Consider URL query-state for search terms if users need shareable filtered views.
- Keep the PR description aligned with the final behavior so reviewers can verify intent quickly.

### Confidence score: High
