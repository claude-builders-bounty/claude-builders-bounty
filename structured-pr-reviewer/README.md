# Structured PR Reviewer

`claude-review` is a Claude Code-friendly CLI that takes a GitHub PR URL, fetches the diff, analyzes it, and prints a structured Markdown review comment.

It works with the required interface:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

## Output format

The review always includes:

- Summary of changes, 2-3 sentences
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

## Setup

```bash
chmod +x structured-pr-reviewer/claude-review
sudo cp structured-pr-reviewer/claude-review /usr/local/bin/claude-review
```

If GitHub CLI is installed and authenticated, `claude-review` uses it. Otherwise it falls back to the GitHub REST API. For higher API limits without `gh`, set:

```bash
export GITHUB_TOKEN=ghp_your_token
```

## Usage

Print to stdout:

```bash
claude-review --pr https://github.com/cli/cli/pull/10000
```

Write to a file:

```bash
claude-review --pr https://github.com/cli/cli/pull/10000 --output review.md
```

Post as a GitHub PR comment:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
gh pr comment https://github.com/owner/repo/pull/123 --body-file review.md
```

## How it reviews

The CLI inspects:

- Changed files and line counts
- Large diffs
- Test presence
- SQL/migration changes
- CI workflow changes
- Dependency changes
- Possible hard-coded secrets
- Risky SQL such as `DELETE FROM` without `WHERE`
- XSS/dynamic execution indicators such as `dangerouslySetInnerHTML`, `eval`, or `new Function`

The output is deterministic, automation-safe Markdown. It is designed to be used directly by Claude Code or inside a GitHub Action step.

## Sample outputs

See:

- `samples/review-claude-builders-1472.md`
- `samples/review-claude-builders-1473.md`
