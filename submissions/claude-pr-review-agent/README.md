# Claude PR Review Agent

A self-contained CLI and GitHub Action that reviews a pull request diff and emits a structured Markdown review comment.

Bounty target: Claude Builders Bounty #4.

## Features

- CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- Fetches PR metadata and diff from GitHub
- Produces structured Markdown with:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence score
- Works without an LLM key using deterministic heuristics
- Optionally uses Anthropic Claude when `ANTHROPIC_API_KEY` is set
- Includes a GitHub Action workflow example

## Setup

```bash
python3 -m pip install -e ./submissions/claude-pr-review-agent
export GITHUB_TOKEN=ghp_xxx   # optional but recommended for rate limits
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Optional Claude mode:

```bash
export ANTHROPIC_API_KEY=sk-ant-xxx
claude-review --pr https://github.com/owner/repo/pull/123 --use-claude
```

Write output to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## GitHub Action

Copy `.github/workflows/claude-review.yml` into a repo. On pull requests, it runs the reviewer and posts the Markdown output as a PR comment.

Required secrets:

- `GITHUB_TOKEN`: automatically provided by GitHub Actions
- `ANTHROPIC_API_KEY`: optional. If absent, the action uses deterministic review heuristics.

## Acceptance Criteria Mapping

- CLI works with `claude-review --pr <url>`
- GitHub Action workflow included
- Structured Markdown output includes summary, risks, suggestions, confidence
- Two real PR sample outputs included under `samples/`
- Setup and usage documented
