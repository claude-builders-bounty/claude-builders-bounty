# Claude Review Agent

Structured PR review helper for bounty #4.

## Setup

1. Install GitHub CLI and authenticate: `gh auth login`.
2. Put `bin/claude-review` on PATH or run it directly.
3. Run: `./bin/claude-review --pr https://github.com/owner/repo/pull/123`.

## Usage

```bash
./bin/claude-review --pr https://github.com/cli/cli/pull/12345
./bin/claude-review --pr https://github.com/owner/repo/pull/123 --post
```

Output includes:
- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

`--post` publishes the generated Markdown as a PR comment via `gh pr comment`.
