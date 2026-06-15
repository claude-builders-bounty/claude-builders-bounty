# PR Review: vercel/next.js#65821

**feat: add support for `unstable_after` in Pages Router**

---

## Summary
This PR adds the `unstable_after` API to the Pages Router, bringing it to parity with the App Router implementation introduced in Next.js 14.1. The implementation hooks into the existing response lifecycle and defers callback execution until after the response is sent to the client.

## Risks
- The `unstable_` prefix correctly signals instability, but the Pages Router implementation diverges from the App Router in how it handles error boundaries — if the deferred callback throws, there is no equivalent of React's error boundary to catch it; errors will surface as unhandled promise rejections in the Node.js process
- `after()` callbacks that reference `req`/`res` objects may execute after those objects are garbage-collected in some edge runtime configurations — the PR doesn't add a guard for this case
- The test suite only covers the Node.js runtime; edge runtime behavior is untested

## Suggestions
- Add a try/catch wrapper around the deferred callback invocation and route errors to `console.error` at minimum, since there's currently no way for application code to handle these failures
- Consider adding a warning when `after()` is called with an async function that captures `req` or `res` — these are the most common source of use-after-free bugs with deferred callbacks
- The `packages/next/src/server/after.ts` implementation duplicates logic already in `packages/next/src/server/app-render/after-task-runner.ts` — worth extracting to a shared utility before this API stabilizes

## Confidence
**Overall assessment**: Request Changes  
**Confidence**: Medium  
**Reason**: The core implementation looks correct for the happy path, but the error handling gap in deferred callbacks is a real reliability concern for production use.
