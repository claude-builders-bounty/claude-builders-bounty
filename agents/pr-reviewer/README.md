# Claude PR Reviewer Agent

`claude-review` is a stdlib-only CLI that reads a GitHub pull request diff and returns a structured Markdown review comment.

It is designed for Claude Code workflows where a deterministic local pass is useful before a human or LLM reviewer does deeper semantic review.

## Setup

No package install is required. Add this directory to your `PATH`:

```bash
export PATH="$PWD/agents/pr-reviewer:$PATH"
```

Then run:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

You can also review a local diff:

```bash
claude-review --diff-file /tmp/example.diff
```

## Usage

Write the review to a Markdown file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

The output includes:

- Summary of changes
- Files changed with added/deleted line counts
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High
- Review notes and assumptions

## Review Signals

The reviewer scans for patterns that commonly need closer inspection:

- GitHub Actions `pull_request_target`, secret usage, and missing minimal `permissions`
- Shell scripts without `set -euo pipefail`
- Destructive shell commands and remote script piping
- JavaScript/TypeScript `eval`, broad `any`, and `dangerouslySetInnerHTML`
- Python broad exception handling and `subprocess(..., shell=True)`
- SQL, schema, and migration changes
- Code changes that do not include test updates

## Samples

Two sample outputs generated from real pull requests are included in `samples/`.
