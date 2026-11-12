# PR Review — [Revert caching a default SSLContext](https://github.com/psf/requests/pull/6767)

## Summary
The change removes the cached default SSLContext optimization and restores CA-bundle selection in the adapter's TLS verification path. It changes certificate-location handling while retaining the explicit unverified-request branch.

## Risks
- No configured high-signal risk patterns were detected in added lines. This does not guarantee the change is safe.

## Suggestions
- Add or update tests for default CA bundle selection, custom CA file/directory paths, missing CA paths, and verify=False behavior; the inspected PR changes only the adapter source file.

## Confidence
**Medium** — The diff is limited to one source file, but no test/spec path appears in the PR. Automated pattern checks cannot establish TLS correctness.

_Generated from the public PR diff by the Sovereign PR Review sample workflow._
