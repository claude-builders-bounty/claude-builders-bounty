# PR Review Agent

A Claude Code sub-agent that reviews GitHub pull requests and produces a structured Markdown report.

## Features

- Fetches PR metadata and diff via the `gh` CLI
- Analyzes changed files for:
  - **Code quality** — bare exceptions, mutable defaults, TODO/FIXME density
  - **Security** — hardcoded secrets, SQL injection, command injection patterns
  - **Performance** — large diff warnings
  - **Type safety** — use of `any` / untyped signatures
  - **Test coverage** — ratio of test files to source files
- Outputs a clean, categorized Markdown review
- Handles large diffs, empty diffs, and binary-only changes gracefully

## Usage

### As a Claude Code sub-agent

With `agent-config.json` in your project, run:

```
/review-pr 123
/review-pr https://github.com/owner/repo/pull/123
/review-pr owner/repo/123
```

### Standalone

```bash
export GITHUB_TOKEN="ghp_..."
chmod +x pr-review-agent.sh
./pr-review-agent.sh 123
```

The review is written to `./pr-reviews/pr-review-<owner>-<repo>-<n>.md` and printed to stdout.

### Environment variables

| Variable              | Default                       | Description                       |
|-----------------------|-------------------------------|-----------------------------------|
| `GITHUB_TOKEN`        | —                             | GitHub token for API access       |
| `REVIEW_TEMPLATE`     | `./review-template.md`        | Path to the review Markdown template |
| `PR_REVIEW_OUTPUT_DIR`| `./pr-reviews`                | Directory to write review output  |

### As a GitHub Action (optional)

See [`action.yml`](./action.yml) for a complete self-contained Action.

## Requirements

- `gh` CLI (authenticated)
- `python3` (for JSON parsing)
- `bash` ≥ 4.0

## Customisation

Edit `review-template.md` to change the output structure. All template variables use `{{VARIABLE}}` syntax.

To enable deeper analysis, wire in linters (e.g. `ruff`, `eslint`, `golangci-lint`) instead of the built-in heuristic scanner.

## Limitations

- Heuristic analysis is pattern-based and may produce false positives/negatives
- Full static analysis via linters is recommended for production use
- Very large PRs (>2000 diff lines) are summarised with a warning
