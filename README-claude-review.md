# Claude PR Review Agent

A dependency-free CLI that generates a structured Markdown review comment from a GitHub pull request diff.

This addresses bounty #4: it works as `claude-review --pr https://github.com/owner/repo/pull/123` and returns:

- a 2-3 sentence summary of changes
- identified risks
- improvement suggestions
- a Low / Medium / High confidence score

## Setup

```bash
chmod +x claude-review
```

The `--pr` mode uses the GitHub CLI to fetch diffs, so make sure `gh` is installed and authenticated for private repositories. Public repositories can also be reviewed when `gh` can access them.

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

For offline testing, review a local diff file instead:

```bash
gh pr diff 123 --repo owner/repo > /tmp/pr.diff
./claude-review --diff-file /tmp/pr.diff
```

## Output format

The command prints Markdown suitable for a PR comment:

```markdown
# Structured PR Review for https://github.com/owner/repo/pull/123

## Summary of changes
...

## Identified risks
...

## Improvement suggestions
...

## Confidence score: Medium
```

## How it works

The CLI performs a first-pass static diff review:

1. Fetches the PR diff with `gh pr diff`.
2. Counts changed files, additions, and removals.
3. Classifies touched areas as code, tests, docs, or assets from file paths.
4. Flags risk patterns such as shell execution, destructive SQL/shell strings, credential-like terms, network calls, and privilege-sensitive commands.
5. Emits a structured Markdown checklist for maintainers.

This is intentionally conservative. It does not replace human review or CI, and it does not post comments automatically.

## Tested sample PRs

Sample outputs generated from two real GitHub PRs are included in:

- `sample-outputs/pr-886-review.md`
- `sample-outputs/pr-888-review.md`

Commands used:

```bash
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/886 > sample-outputs/pr-886-review.md
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/888 > sample-outputs/pr-888-review.md
```
