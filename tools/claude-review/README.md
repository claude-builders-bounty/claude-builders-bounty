# claude-review

`claude-review` generates a structured Markdown review comment from a GitHub pull request diff.

It is intentionally a small Claude Code agent helper: run it locally, inspect the output, then paste the Markdown into the PR or use it as the starting point for a richer Claude Code review session.

## Usage

```bash
tools/claude-review/claude-review --pr https://github.com/owner/repo/pull/123
```

The command prints:

- a 2-3 sentence summary of the change
- identified risks
- improvement suggestions
- a confidence score of `Low`, `Medium`, or `High`

## Requirements

- Python 3
- GitHub CLI authenticated with read access to the target pull request

No paid API key is required for the default heuristic pass.

## Review model

The agent fetches PR metadata and the unified diff with `gh api`, classifies changed files and added lines, then emits a Markdown review that is predictable enough to use in automation.

It intentionally avoids posting comments itself. That keeps the workflow safe: humans or higher-level agents can review the generated Markdown before publishing.

## Validation

Two real PR outputs are included under `samples/claude-review/`:

- `pr-1374-output.md`
- `pr-1381-output.md`

Run the smoke test:

```bash
tools/claude-review/test-claude-review.sh
```
