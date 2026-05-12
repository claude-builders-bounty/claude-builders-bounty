# Claude PR reviewer CLI

`claude-review` reviews a GitHub pull request diff and prints a structured Markdown comment.

## Install

```bash
cp bin/claude-review ~/.local/bin/claude-review
chmod +x ~/.local/bin/claude-review
```

Optional for higher GitHub API limits:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Output sections:

- summary of changes
- identified risks
- improvement suggestions
- confidence score: Low, Medium, or High

## What it checks

The reviewer performs a static diff review for common issues:

- possible secrets in added lines
- TODO/FIXME markers
- debug statements
- broad or empty error handling
- dependency file changes
- large changes without obvious tests

It is intentionally deterministic and dependency-free so it can run in CI or locally with Python 3.10+.

## Sample outputs

See:

- `samples/pr-reviewer/sxt-proof-of-sql-1441.md`
- `samples/pr-reviewer/claude-builders-1127.md`

## CI/GitHub Action usage

A workflow can run:

```yaml
- name: Review PR
  run: python bin/claude-review --pr "${{ github.event.pull_request.html_url }}" > review.md
```

Posting the comment can be done with `gh pr comment` or `actions/github-script` depending on repository policy.
