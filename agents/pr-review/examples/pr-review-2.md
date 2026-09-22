PR: https://github.com/psf/requests/pull/6710
Head: `92075b330a30b9883f466a43d3f7566ab849f91b` | Base: `970e8cec988421bd43da57350723b05c8ce8dc7e`
Diff SHA-256: `4667990ef0604b40fea939d9c0fae4e00f35665c58922d8972336b6d63d96552`
Review backend: Recorded response from GPT-6 Astra Pro \(ChatGPT session\); NOT a live Claude run

## Summary

This change promotes the TLS-aware connection-selection hook to get\_connection\_with\_tls\_context and updates HTTPAdapter.send to call that public hook. It retains get\_connection but documents its deprecation, emits a DeprecationWarning when the base implementation is called, and documents the replacement hook for adapter subclasses.

## Risks

- src/requests/adapters.py:555-557 changes the dispatch point, so downstream adapters that overrode \_get\_connection will no longer intercept send through that override; this is a compatibility risk that should be covered by migration documentation and tests.
- src/requests/adapters.py:429-437 emits a warning only when the base get\_connection implementation is actually called, so subclasses bypassed by the new dispatch will not necessarily receive this warning.
- src/requests/adapters.py:389 describes cert as a certificate to be trusted, which can confuse client authentication with the trust-store verification controlled by verify.
- The patch contains no tests demonstrating new-hook dispatch, argument forwarding, or the deprecation-warning behavior.

## Improvement Suggestions

- Set stacklevel=2 on warnings.warn so the warning points at the caller instead of the adapter implementation.
- Add an adapter subclass test asserting that send calls get\_connection\_with\_tls\_context exactly once and forwards the original request, verify, proxies, and cert values.
- Document migration for subclasses overriding either the old public get\_connection or the formerly private \_get\_connection, and warn that a URL-only pass-through may discard TLS-specific connection-pooling behavior.
- Clarify the cert parameter documentation to identify client-certificate and optional key inputs, separately from verify and CA-bundle trust configuration.
- Add a warning assertion for direct calls to the deprecated method and a compatibility test for the intended subclass migration path.

## Confidence

Medium

---
Scope: metadata and diff only. No PR code or tests were executed.
