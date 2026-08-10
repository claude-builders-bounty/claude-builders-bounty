# claude-review 🤖

A **Claude Code sub-agent** that reviews a GitHub PR and posts a structured Markdown comment.

Takes a PR URL as input, fetches the diff from the GitHub API, analyzes it for common
risks and improvement opportunities, and outputs a structured review containing:

- **Summary** of changes (2–3 sentences)
- **Identified risks** (list, with severity)
- **Improvement suggestions** (list)
- **Confidence score**: Low / Medium / High

## Features

- ✅ Works via CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- ✅ Works via GitHub Action (workflow YAML included)
- ✅ Structured Markdown output
- ✅ Zero external dependencies (stdlib only) — no API key required
- ✅ Tested on real GitHub PRs (see `samples/`)

## Setup

```bash
# 1. Install
pip install .

# 2. (Optional) Provide a GitHub token for higher rate limits
export GITHUB_TOKEN=ghp_xxx
```

## Usage (CLI)

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Write to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Usage (GitHub Action)

Add the workflow to your repo (`.github/workflows/review.yml` is included in this
project). It runs automatically on every PR and posts the review as a comment:

```yaml
name: claude-review
on:
  pull_request:
    types: [opened, synchronize, reopened]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install .
      - run: claude-review --pr "${{ github.event.pull_request.html_url }}" --output review.md
        env: { GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} }
      - run: gh pr comment "${{ github.event.pull_request.html_url }}" --body-file review.md
        env: { GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} }
```

## Output Example

```markdown
## 🤖 claude-review

**PR:** https://github.com/owner/repo/pull/123
**Title:** Fix login flow

### Summary
This PR touches 3 file(s) with 45 additions and 12 deletions. The review
identified 2 potential risk(s) worth addressing. Overall the change is focused
and reviewable.

### Identified Risks
- **[HIGH] Hardcoded secret / credential** — `auth.py:14`
  - `api_key = "sk-1234567890abcdef"`
  - 💡 Move secrets to environment variables or a secret manager.

### Improvement Suggestions
- **No test changes detected** — No test/spec files were modified in this PR.
  - 💡 Consider adding unit tests covering the changed behavior.

### Confidence
**Medium**
```

## Tests

```bash
pip install pytest
pytest
```

## License

MIT