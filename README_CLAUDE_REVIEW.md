# Claude PR Review Agent

A dependency-free CLI and optional GitHub Action that reviews a pull request diff and returns a structured Markdown comment.

## CLI usage

```bash
python3 bin/claude-review --pr https://github.com/owner/repo/pull/123
```

Write to a file:

```bash
python3 bin/claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Offline/local diff test:

```bash
python3 bin/claude-review --pr https://github.com/example/repo/pull/1 --diff-file path/to/pr.diff
```

## GitHub Action

Copy `.github/workflows/claude-review.yml` into a repository. On every opened, synchronized, or reopened pull request it will:

1. Fetch the PR diff.
2. Generate the structured Markdown review.
3. Post it as a PR comment.

## Output format

The review always includes:

- Summary of changes, 2–3 sentence scale and file overview
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

## How it reviews

This is a deterministic Claude Code sub-agent scaffold: it fetches PR context and produces the structured comment Claude can refine or post. The logic intentionally focuses on review triage signals that are cheap and reliable:

- changed files and diff size
- auth/session/permission markers
- database/schema/migration markers
- secret-like terms
- network/API calls
- CI/dependency changes
- whether tests appear to be included

## Test

```bash
python3 -m unittest discover -v
```
