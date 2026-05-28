## PR Review: fix: prevent mass assignment in reviewService by whitelisting fields (#1301)

**Repo:** SecureBananaLabs/bug-bounty | **PR:** #1320

### Summary
This PR fixes a mass assignment vulnerability in the reviewService by replacing the spread operator with explicit field whitelisting. Instead of blindly accepting all fields from the request body, it now only allows `rating` and `comment` properties.

### Identified Risks
- None introduced — this change reduces the attack surface
- Existing callers passing extra fields will silently lose them; no breaking change since those fields weren't used before
- No test coverage was added alongside the fix, so regressions may go undetected

### Improvement Suggestions
- Add unit tests for the whitelist to ensure it rejects unknown fields
- Consider extracting the whitelist pattern into a shared utility function to avoid repetition across services

### Confidence Score
**Confidence: High**
The change is minimal, straightforward, and follows the explicit pattern needed for securing the service. No complex logic or side effects are introduced.
