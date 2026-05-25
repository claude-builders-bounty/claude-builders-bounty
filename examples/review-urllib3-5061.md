## PR Review

### Summary

This PR changes 2 file(s), with 26 additions and 1 deletions. The main touched
areas are `changelog/1362.bugfix.rst`, `src/urllib3/connection.py`,
`src/urllib3/util/response.py`, and
`test/with_dummyserver/test_socketlevel.py`, so review should focus on whether
those edits match the stated intent and preserve existing behavior.

### Identified Risks

- No high-risk file patterns were detected, but reviewer should still verify
  tests cover the changed behavior.

### Improvement Suggestions

- Run the repository's lint, typecheck, and test commands before merge.
- Confirm the PR description includes the user-facing behavior change and manual
  verification notes.

### Confidence: High
