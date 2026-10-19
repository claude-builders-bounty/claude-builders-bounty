# Claude PR reviewer — bounty #4

A dependency-free Python CLI that fetches a GitHub pull request's changed-file patches, asks Claude for a structured code review, and prints Markdown. It **does not post** comments by default. You must explicitly pass --post and supply GITHUB_TOKEN to write.

## Setup and usage

1. Install Python 3.9+, then from this directory run `python3 -m pip install .` to install the **`claude-review`** CLI entry point (or `python3 -m pip install -e .` for local development).
2. Export `ANTHROPIC_API_KEY` in your terminal. For GitHub private repos and optional posting, also export `GITHUB_TOKEN` (fine-grained token with pull-request read and issue-comment write permissions).
3. Run:

   claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4810

   Without installation, use `python3 review_pr.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4810` from this directory.
4. Review the generated output. To publish it, add `--post` explicitly. Only the review is posted; no code is changed. Offline tests: `python3 -m unittest discover -s . -p "test_review_pr.py" -v`.

## Output

- Summary in 2–3 sentences
- Identified risks (bullets)
- Improvement suggestions (bullets)
- Confidence: Low / Medium / High

The tool asks Claude for JSON and validates the response before formatting. Full PR file patches are fetched using pagination, up to 300 files and 60,000 characters; lengthy diffs are **marked truncated** and must lower confidence. Binary files cannot be reviewed from patches. Repository PR content is untrusted and placed inside a data payload; prompt injection remains a residual LLM risk.

Uses Anthropic Messages API and defaults to claude-sonnet-4-20250514. API calls can cost money and require an Anthropic key; test suite uses HTTP mocks and costs nothing. The tool does **not** run commands found in a pull request and does not transmit GitHub or Anthropic keys in prompts.

## Verification and honest limitations

- Offline automated tests cover URL sanitization, safe-by-default behavior, response parsing and HTTP adapter boundaries.
- EXAMPLES.md contains **two manual code-review examples** based on actual public PR diffs (#4810 and #4834) to show intended output and discuss relevant risks. They are *not* outputs of a live Claude API run and should not be represented as an end-to-end test.
- Live integration (a Claude API key and two authenticated live executions) is still necessary to demonstrate full compliance with bounty #4's two-real-PRs testing criterion.

No external dependencies, install hooks, auto-posting, or executable code taken from the PR diff.
