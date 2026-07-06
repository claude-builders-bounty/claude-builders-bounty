# Claude PR review agent

`claude-review` is a local Claude Code-style PR review agent. It accepts a
GitHub pull request URL, reads the public PR metadata and changed files, then
prints a structured Markdown review comment.

It does not require the Claude API, paid services, wallet signatures, or any
write access to GitHub. Set `GITHUB_TOKEN` only if you need a higher GitHub API
rate limit for public repositories.

## Setup

```bash
chmod +x bin/claude-review
export PATH="$PWD/bin:$PATH"
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

The output includes:

- Summary of changes in 2-3 sentences.
- Identified risks.
- Improvement suggestions.
- Confidence score: `Low`, `Medium`, or `High`.

The agent scores confidence from PR size, touched areas, sensitive paths, and
visible test coverage. It highlights risks such as missing tests, CI workflow
changes, dependency files, migrations, auth/security paths, and very large diffs.

## Samples

Two real GitHub PR outputs are included:

- `samples/claude-review-pr-3228.md`
- `samples/claude-review-pr-3229.md`
