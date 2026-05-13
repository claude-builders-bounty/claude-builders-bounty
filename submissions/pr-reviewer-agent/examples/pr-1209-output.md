## Summary

This PR introduces `claude-review`, a Python CLI tool that fetches a public GitHub PR diff, applies static-analysis heuristics to detect risky patterns (e.g., `shell=True`, hard-coded secrets, `eval`/`exec`, destructive commands), and outputs a structured Markdown review. It includes a new CLI script, unit tests, sample outputs, and README documentation.

## Identified risks

- `fetch_pr_diff` in `claude_review.py` does not handle HTTP errors (e.g., 404 for private repos, 403 rate limits, 5xx). A non-200 response from `urlopen` will raise an `URLError` caught only by the broad `except Exception` in `main()`, surfacing a confusing error message to the user.
- The secret detection regex `(?i)(secret|api[_-]?key|password|token)\w*\s*=\s*['\"][^'\"]+['\"]` may produce false positives on benign assignments (e.g., `token = "placeholder"`, test fixtures, or example config) and false negatives on values loaded from environment variables or configuration files at runtime.
- The confidence scoring logic (`"High" if risks or files else "Low"`) marks any non-empty PR as "High" confidence regardless of risk severity or diff complexity, which may overstate reliability.
- Destructive pattern matching (`rm -rf`, `drop table`, `truncate table`, `delete from`) is applied across all added lines without excluding non-code contexts (e.g., documentation, comments, or test data), risking false alarms.
- No retry or timeout adjustment exists for transient network failures; the 30-second timeout is fixed with no backoff.
- The tool lacks GitHub token support, limiting it to public repositories only, with no clear error path for private PRs.

## Improvement suggestions

- Replace the broad `except Exception` in `main()` with targeted exception handling (e.g., `ValueError` for URL parsing, `urllib.error.HTTPError`/`URLError` for network failures) to surface actionable error messages.
- Add HTTP error handling in `fetch_pr_diff` to distinguish between 404 (PR not found or private), 403 (rate limited), and network errors, possibly with retry logic and exponential backoff.
- Tighten the secret detection heuristic by excluding lines containing common placeholder values (e.g., `"xxx"`, `"changeme"`, `"your_key_here"`) and by skipping test or sample files.
- Refine the confidence scoring to account for diff size, number of flagged risks, and presence of test files rather than a simple binary check.
- Optionally add a `--token` flag for authenticated diff fetching to support private repositories.

## Confidence

High - the diff is self-contained, readable, and includes unit tests covering the core parsing, analysis, formatting, and fetch functions, making the behavior and limitations clear to assess.
