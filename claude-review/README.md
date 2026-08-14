# Claude PR review agent

`claude-review` fetches a public pull-request summary and file patches through
GitHub's read-only API, then emits a structured Markdown review with a summary,
risks, suggestions, and a confidence score. It uses only Python's standard
library and does not need a GitHub token for public PRs.

## Usage

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123
```

To save a review, add `--output review.md`. Set `GITHUB_TOKEN` only when the
public API rate limit is reached; the tool never prints or stores the token.
The deterministic checks are triage assistance, not a substitute for a human
security review.
