## Summary
This PR adds support for sending payments to BOLT12 offers in the LNbits wallet interface. It introduces a new `handle_send_bolt12()` method, updates the send modal UI to detect BOLT12 offer strings, and integrates with the underlying Lightning infrastructure. The change touches 7 files with ~300 lines of new code and minimal deletions.

## Identified Risks
- **BOLT12 support varies by backend**: Not all Lightning backends support BOLT12 offers. The PR should handle cases where the backend returns an unsupported error gracefully rather than crashing.
- **Input validation**: BOLT12 offer strings have a specific format — if validation is too loose, invalid offers could reach the backend and produce confusing error messages for users.
- **Edge case — expired offers**: BOLT12 offers can expire. The PR should display a clear message if an offer is no longer valid.

## Improvement Suggestions
- Add a backend capability check before showing the BOLT12 send option in the UI to avoid confusion on backends that don't support it.
- Consider adding unit tests for BOLT12 offer string parsing/validation.

## Confidence Score
**Confidence: Medium**

The changes are logically structured and follow existing patterns in the codebase, but the correctness depends on backend-specific BOLT12 support which isn't fully testable in isolation.
