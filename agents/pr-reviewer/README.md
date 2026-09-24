# claude-review — PR reviewer for Claude Code

A one-command PR reviewer: it fetches a GitHub pull-request diff and asks Claude
Code to produce a structured Markdown review (summary, risks, suggestions, and a
confidence score).

## Setup (3 steps)

1. Install [Claude Code](https://claude.ai/code) and confirm `claude` is on your `PATH`.
2. Make the script executable: `chmod +x claude-review`
3. (Private repos only) export a GitHub token: `export GH_TOKEN=...`

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

Output is structured Markdown:

```
## Summary
...
## Identified risks
- ...
## Improvement suggestions
- ...
## Confidence
High — ...
```

## How it works

1. Parses the PR URL into `owner`, `repo`, and `number`.
2. Fetches the unified diff from the GitHub API
   (`Accept: application/vnd.github.v3.diff`).
3. Builds a review prompt and pipes it to `claude -p`.

## Sample outputs

- [`samples/pr-4473-review.md`](samples/pr-4473-review.md)
- [`samples/pr-4475-review.md`](samples/pr-4475-review.md)
