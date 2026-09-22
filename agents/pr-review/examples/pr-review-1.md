PR: https://github.com/psf/requests/pull/6731
Head: `da96a92e2eb6dfe7c74704267bcb8f9fd6fb92b0` | Base: `0e322af87745eff34caffe4df68456ebc20d9068`
Diff SHA-256: `919f69cfd2b52d8e13283200e42a142956ea8a825369f7770b37deeec3dde8a6`
Review backend: Recorded response from GPT-6 Astra Pro \(ChatGPT session\); NOT a live Claude run

## Summary

This change restricts reuse of the preloaded SSL context to requests that verify certificates and do not supply a client certificate or an existing pool-manager SSL context. It also supplies the default CA bundle when verification is enabled but the preloaded context is not selected, while preserving separate file and directory handling for explicit CA paths.

## Risks

- src/requests/adapters.py:126-136 adds the default CA bundle whenever verify is True and the shared context is not selected, including when the pool manager already supplies an SSL context; verify that this does not unexpectedly extend a caller-configured trust store, because the actual effect depends on urllib3 code outside this diff.
- src/requests/adapters.py:128-136 introduces a CA-path selection path without the validation performed by cert\_verify, so missing or invalid default-bundle paths may produce different errors across these paths.
- The diff changes only adapters.py and includes no regression tests for the client-certificate concurrency problem or the default-CA fallback described in the PR.

## Improvement Suggestions

- Add a table-driven test covering verify=True, verify=False, CA files, CA directories, client-certificate strings and pairs, an existing pool-manager SSL context, and an unavailable preloaded context.
- Add a local TLS regression test that alternates different client certificates across requests and checks that the shared preloaded SSL context is not mutated or reused in that case.
- Test a caller-supplied SSL context with a restricted trust store and document whether adding the default CA bundle is intentional before accepting the new fallback.
- Keep CA-path selection and validation consistent between \_urllib3\_request\_context and cert\_verify, including errors for missing paths, without changing the existing public exception contract.

## Confidence

Medium

---
Scope: metadata and diff only. No PR code or tests were executed.
