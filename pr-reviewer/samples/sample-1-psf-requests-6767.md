### 🤖 Claude PR Review

## Summary
This PR reverts #6667 and removes the module-level preloaded default `SSLContext` in `requests/adapters.py`. `cert_verify` goes back to resolving the default CA bundle path (via `extract_zipped_paths(DEFAULT_CA_BUNDLE_PATH)`) and setting `conn.ca_certs` or `conn.ca_cert_dir` on each connection. `_urllib3_request_context` no longer injects a shared `ssl_context`.

## Risks
- Performance regression is intentional. Each new HTTPS connection with `verify=True` loads the CA bundle again, which is slow, particularly on the first request and for many short-lived sessions.
- `cert_verify` raises `OSError` again if the default bundle is missing or invalid. That is the old behavior, but anyone who relied on the post-#6667 behavior could see failures. This includes environments where certifi's bundle is absent but an `ssl_context` is supplied.
- The `verify is True` branch is removed from `_urllib3_request_context`. If `verify` is `True`, nothing is set in `pool_kwargs` for `ca_certs`. The connection then depends on `cert_verify` to set the CA location, so `get_connection_with_tls_context` and `cert_verify` must stay consistent. I can't confirm that from the diff alone.
- Unused imports are possible after the removal, such as `extract_zipped_paths` and `DEFAULT_CA_BUNDLE_PATH`. Both are still used in `cert_verify`, so this is probably fine, but I couldn't check it.
- Tests added with #6667, such as ones for the preloaded context or for avoiding `load_verify_locations`, may now fail or be stale. The diff doesn't show whether they were removed or adjusted.
- Because #6667's changes were reverted wholesale, anything built on them after it merged could break. This includes the changelog entry and other code that references `_preloaded_ssl_context`.
- The PR description says there were concurrency edge cases. The revert removes the shared mutable context, which addresses those cases. The diff has no regression test showing the original issues are gone.

## Suggestions
- Run `grep` for `_preloaded_ssl_context` across the repo, including tests and docs, to confirm that nothing still references it.
- Remove or update the tests and changelog entries from #6667 so the test suite matches the reverted behavior.
- Add a short HISTORY/changelog note saying the caching was reverted and why, so users who saw the speedup know it is gone.
- Run the full test suite, including tests that use `verify=True`, `verify=<path>` and `verify=<dir>`, and the proxy and SOCKS tests, against the final tree.
- If the caching is revisited later, put the design in an issue first, with a concurrency and fork-safety test plan, as the description says.

## Confidence
Medium: the diff is small and clear, but I couldn't see the surrounding code, the tests, or what #6667 originally changed.

---
_Automated review of https://github.com/psf/requests/pull/6767 by claude-review. Verify before acting._
