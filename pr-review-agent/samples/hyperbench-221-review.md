## 📋 PR Review — hyperbench #221: fix: add timeout=10 to get_gh_dataset_sha request

### Summary
This PR adds a 10-second timeout parameter to the `requests.get()` call in `get_gh_dataset_sha()`, which queries the GitHub API for dataset commit SHAs. The corresponding test assertions are updated to verify the timeout parameter is passed correctly. This is a defensive fix to prevent indefinite hangs when the GitHub API is unresponsive.

### ⚠️ Identified Risks
- **No significant risks identified** — The change is minimal and focused. Adding a timeout is universally good practice for HTTP calls.

### 💡 Improvement Suggestions
- **Consider a configurable timeout** — Hardcoding `timeout=10` works for most cases, but in CI environments with high latency or corporate proxies, 10 seconds might be tight. Consider using a module-level constant (e.g., `GITHUB_API_TIMEOUT = 10`) or an environment variable for easier tuning without code changes.
- **Apply timeout consistently across all GitHub API calls** — This PR only fixes `get_gh_dataset_sha()`. If `hif_utils.py` has other `requests.get()` calls to GitHub API, they should also receive timeout parameters to prevent similar hanging issues. A quick grep shows `get_gh_datasets_shas()` likely calls the same function, so it's covered, but worth auditing the entire codebase.
- **Test with timeout simulation** — The current tests mock `requests.get` but don't test the timeout behavior itself (e.g., what happens when a `Timeout` exception is raised). Adding a test case where `requests.get` raises `requests.exceptions.Timeout` would verify the error handling path.
- **Consistent line formatting** — The test file changes include some reformatting (multi-line `patch()` calls). This is good for readability but should be done via `ruff format` consistently across the project to avoid mixed styles.

### 🎯 Confidence Score
**High** — The diff is very focused (1 functional change + test updates + formatting). The timeout addition is straightforward and the test coverage is adequate for the scope of this change.
