# Claude PR review agent

`claude-review` is a lightweight pull request review agent for Claude Code workflows.

It accepts a GitHub pull request URL, fetches the PR metadata and diff, then returns a structured Markdown review with:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score

If the `claude` CLI is installed, the tool can hand the review prompt to Claude Code directly. If not, it falls back to a local heuristic reviewer so the CLI still works out of the box.

## Setup

```bash
chmod +x ./claude-review
```

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

Write to a file:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --output samples/review.md
```

Force the local heuristic path:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --heuristic
```

## Sample outputs

Two real PR review outputs are included in `samples/`:

- `samples/claude-builders-bounty-pr-333.md`
- `samples/jhipster-generator-jhipster-pr-32638.md`

## GitHub Action

The repository includes `.github/workflows/pr-review-agent.yml`, which can be triggered manually with a PR URL and uploads the generated Markdown as an artifact.
