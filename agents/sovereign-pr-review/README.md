# Sovereign PR Review

A GitHub pull-request reviewer that produces structured Markdown with findings linked to exact changed-file lines.

## Features
- CLI accepts a GitHub PR URL.
- Deterministic standard-library mode; no paid model key required.
- Optional Anthropic analysis when ANTHROPIC_API_KEY is configured.
- Scans added lines only, not unchanged legacy code.
- Findings include severity, file, new-side line, evidence, and rationale.
- Confidence reflects test-path coverage and change scope; it does not claim correctness.
- Comment posting is opt-in on the CLI.

## Setup
Python 3.10+ and a GitHub token with read access are required.

    export GH_TOKEN=github_pat_...
    python3 agents/sovereign-pr-review/claude_review.py --pr https://github.com/owner/repo/pull/123

Optional model-assisted analysis:

    export ANTHROPIC_API_KEY=...
    python3 agents/sovereign-pr-review/claude_review.py --pr https://github.com/owner/repo/pull/123

Save or explicitly post the result:

    python3 agents/sovereign-pr-review/claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
    python3 agents/sovereign-pr-review/claude_review.py --pr https://github.com/owner/repo/pull/123 --post-comment

Force deterministic mode with --no-ai.

## GitHub Action
Copy .github/workflows/sovereign-pr-review.yml into the target repository. It uses pull_request_target so fork PRs can receive review comments. Crucially, it does not check out or execute contributor-controlled PR code: the script comes from the trusted base branch, and the diff is fetched as untrusted data through the GitHub API.

Set ANTHROPIC_API_KEY as an Actions secret to enable optional model review. Without it, deterministic review still runs.

## Sample reviews

Two real public pull requests were inspected and included under samples/: pallets/click#2800 and psf/requests#6767.

## Limitations
Static patterns are triage signals, not proof of vulnerabilities. Absence of a finding does not establish safety. Confidence describes the evidence available to this tool, not the correctness of the PR. Human review and CI remain necessary.

## Tests
Run: python3 -m unittest discover -s tests -v
