# Claude Review Agent

`claude-review` generates a structured Markdown review draft for a GitHub pull request without using a paid API.

## Setup

1. Install and authenticate the GitHub CLI: `gh auth status`.
2. Run from this repository: `./claude-review --pr https://github.com/owner/repo/pull/123`.
3. Paste or save the Markdown output for maintainer review.

## What It Reports

- A 2-3 sentence summary of the changed files and review surface.
- Identified risks such as auth/session changes, database migrations, dependency changes, scripts, generated files, large diffs, missing tests, and suspicious added lines.
- Improvement suggestions tailored to the detected risks.
- Confidence score: Low, Medium, or High.

## Why It Avoids Paid APIs

The agent uses `gh pr view` and `gh pr diff`, then applies deterministic local rules. This keeps the tool usable in local CI, contributor machines, and restricted environments where API keys should not be required.

## Examples

Sample outputs are included in:

- `samples/sample-output-1.md`
- `samples/sample-output-2.md`

## Verification

```bash
python3 -m unittest discover -s pr-review-agent/tests
python3 pr-review-agent/claude_review.py --help
./claude-review --help
git diff --check
```
