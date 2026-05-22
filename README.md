# Claude PR Reviewer

`claude-review` fetches a GitHub PR diff and prints a structured Markdown review
comment for Claude Code or a human reviewer.

## Setup

```bash
chmod +x bin/claude-review
```

## Usage

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123
```

For offline tests or saved diffs:

```bash
bin/claude-review --diff-file tests/fixtures/sample.diff
```

## Output

The review contains a short summary, identified risks, improvement suggestions,
and a Low/Medium/High confidence score. The tool only prints Markdown; it never
posts comments or mutates GitHub state.

## Samples

Two real GitHub PR review outputs are included in `samples/`.
