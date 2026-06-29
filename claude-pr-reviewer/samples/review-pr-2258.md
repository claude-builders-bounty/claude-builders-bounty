## PR Review

### Summary
This PR adds a conservative JSON body size limit to the API layer, touching `apps/api/src/index.ts` and a new middleware test file. The change is small and test-focused, which limits blast radius while enforcing request size bounds at the edge. Overall review confidence is **High** because the diff is narrow and includes automated tests.

### Identified risks
- No high-risk patterns detected in the diff heuristics.

### Improvement suggestions
- Confirm the limit value matches product expectations for largest legitimate payloads.

### Confidence score: High
