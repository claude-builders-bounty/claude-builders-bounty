# Claude PR Review Agent

`claude-review` is a small Claude Code-style review agent that accepts a GitHub pull request URL, fetches PR metadata and changed files from the GitHub API, and prints a structured Markdown review comment.

## Setup

```sh
chmod +x pr-review-agent/bin/claude-review
```

Optionally copy it onto your path:

```sh
cp pr-review-agent/bin/claude-review ~/.local/bin/claude-review
```

## Usage

```sh
pr-review-agent/bin/claude-review --pr https://github.com/owner/repo/pull/123
```

The output contains:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: `Low`, `Medium`, or `High`

## Notes

- Public pull requests work without a GitHub token.
- Private repositories can be supported by adding an `Authorization` header in `github_get_json()`.
- The agent is intentionally deterministic so it is safe to run in CI or inside Claude Code automation before posting the generated Markdown as a PR comment.
