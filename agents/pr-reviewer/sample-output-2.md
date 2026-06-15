# PR Review: sindresorhus/got#2441

**fix: retry on `ECONNRESET` when using `http2: true`**

---

## Summary
This PR adds `ECONNRESET` to the list of retryable error codes when the `http2` option is enabled. HTTP/2 connections are more prone to `ECONNRESET` due to multiplexing, where a server-initiated stream reset can appear as a connection-level error to the client. The fix is a one-line change with a targeted regression test.

## Risks
- Retrying on `ECONNRESET` with HTTP/2 could mask cases where the server intentionally resets the connection (e.g., rate limiting via RST_STREAM with `ENHANCE_YOUR_CALM`). Non-idempotent requests (POST/PATCH) could be sent twice if the initial request was received but the response reset — though this is mitigated by got's existing `methodRewriting` option
- The test uses a mock TCP server rather than a real HTTP/2 server; a genuine `GOAWAY` frame scenario isn't covered

## Suggestions
- Add a comment in the retry config explaining *why* `ECONNRESET` is included for HTTP/2 specifically — this is non-obvious and future contributors will likely remove it thinking it's a mistake
- Consider respecting `RST_STREAM` error codes from the `http2` session if accessible, to distinguish intentional resets from network errors

## Confidence
**Overall assessment**: Approve  
**Confidence**: High  
**Reason**: The change is minimal, well-targeted, and the test directly reproduces the reported scenario; the theoretical POST-retry risk is acceptable given existing safeguards.
