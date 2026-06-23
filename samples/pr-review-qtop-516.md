## PR review

### Summary

This PR for https://github.com/qtop/qtop/pull/516 changes 2 files with 72 additions and 10 deletions. The main review focus should be tests and behavior coverage, with extra attention to scope control and validation evidence. Overall size is small, so review depth should match the risk rather than only the line count.

### Identified risks

- No obvious high-risk file patterns were detected; still verify the changed behavior manually.

### Improvement suggestions

- Confirm the touched tests fail before the fix or clearly prove the intended behavior.
- List the exact validation commands run in the PR description or follow-up comment.
- Keep follow-up cleanup separate unless it directly supports the reviewed change.

### Confidence score

High
