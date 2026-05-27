# Claude Review Agent

`claude-review` is a dependency-free CLI for reviewing a GitHub pull request and
printing a structured Markdown review comment. It is designed to be used by a
Claude Code agent, but it also works as a standalone reviewer when only a public
GitHub PR URL is available.

## Setup

1. Install Node.js 18 or newer.
2. Run the CLI from this folder:

```bash
node claude-review.mjs --pr https://github.com/owner/repo/pull/123
```

For private repositories or higher rate limits, set `GITHUB_TOKEN` before
running the command.

## Usage

Print a review:

```bash
node claude-review.mjs --pr https://github.com/owner/repo/pull/123
```

Save a review:

```bash
node claude-review.mjs --pr https://github.com/owner/repo/pull/123 --output review.md
```

Post the review as a GitHub PR comment:

```bash
GITHUB_TOKEN=ghp_xxx node claude-review.mjs --pr https://github.com/owner/repo/pull/123 --post-comment
```

Run the local test:

```bash
node test.mjs
```

## Output Format

Every review uses the requested structure:

- Summary of changes, written in 2-3 sentences.
- Identified risks.
- Improvement suggestions.
- Confidence score: `Low`, `Medium`, or `High`.

## Agent Pattern

The companion `AGENT.md` file defines the Claude Code sub-agent instructions.
The CLI handles repeatable mechanics: fetching the PR diff, extracting changed
files, measuring churn, finding common risk signals, and rendering the final
Markdown comment.

## GitHub Action Example

An importable workflow example is included in `github-action.example.yml`.
Copy it into `.github/workflows/claude-review.yml` in a target repository if you
want automatic review comments on pull requests.

## Real PR Checks

The `sample-outputs/` folder contains outputs generated against two public
GitHub PRs:

- `claude-builders-bounty-1041.md`
- `claude-builders-bounty-1042.md`

