# Claude PR Review: Add Claude PR review agent

> PR: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2546

## Summary
This PR adds a dependency-free Python CLI (`claude-review --pr <url>`) that fetches a GitHub PR's metadata and diff via the public API, sends it to Claude, and returns a structured Markdown review with summary, risks, improvement suggestions, and a confidence score. It also includes a Claude Code sub-agent definition, a README, two sample outputs, and unit tests covering URL parsing and output contract validation.

## Identified Risks
- **No rate-limit handling**: GitHub's unauthenticated API rate limit is 60 req/hour; large diffs may hit limits without a `GITHUB_TOKEN` set.
- **Diff truncation is silent**: If the diff exceeds the internal character limit, the truncated portion is dropped with no warning to the reviewer or Claude, potentially causing missed context.
- **API key exposed in process list**: Passing `ANTHROPIC_API_KEY` via environment is standard, but the README should explicitly warn against hardcoding it in scripts.
- **Only 2 unit tests**: Coverage is limited to URL parsing and surface-level output shape; no tests for error paths (HTTP errors, malformed API responses, missing env vars).
- **No GitHub Action**: The bounty accepts CLI *or* GitHub Action; not including an Action means maintainers must run the tool manually on each PR.

## Improvement Suggestions
- Add a `--github-token` flag (fallback to `GITHUB_TOKEN`) and surface a clear warning when running unauthenticated.
- Warn to stderr when diff is truncated: `Warning: diff truncated to N chars`.
- Add error-path tests: what happens on `HTTP 404`, `HTTP 429`, and missing `ANTHROPIC_API_KEY`.
- Include a GitHub Actions workflow YAML so teams can auto-post reviews on `pull_request` events without manual invocation.
- Pin the Claude model in a top-level constant so it's easy to upgrade without hunting through the code.

## Confidence Score
**High** — The PR is well-scoped, the code is straightforward Python using only stdlib + the Anthropic API, and the two sample outputs demonstrate the tool works end-to-end on real PRs.
