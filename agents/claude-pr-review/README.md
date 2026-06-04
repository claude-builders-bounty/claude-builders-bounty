# Claude Code PR Review Agent

A small Claude Code agent that reviews a GitHub pull request and prints a structured Markdown comment.

It satisfies bounty #4 by supporting this CLI shape:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

The output always includes:

- Summary of changes, in 2-3 sentences
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

## Setup

1. Ensure `claude` is installed and authenticated.
2. Add the wrapper to your shell:

```bash
alias claude-review='python3 /absolute/path/to/agents/claude-pr-review/claude_review.py'
```

Optional: set `GITHUB_TOKEN` to increase GitHub API rate limits and allow private repository access.

## Usage

```bash
claude-review --pr https://github.com/octocat/Hello-World/pull/1
```

Write the review to a file:

```bash
claude-review --pr https://github.com/octocat/Hello-World/pull/1 --output review.md
```

Choose a Claude model:

```bash
claude-review --pr https://github.com/octocat/Hello-World/pull/1 --model sonnet
```

## GitHub Action

This repository also includes `.github/workflows/claude-pr-review.yml`. Copy it into a repository and run it manually with a PR URL. It generates `claude-pr-review.md` as an artifact.

The workflow intentionally uses `workflow_dispatch` instead of automatically posting comments. Reviewing code should be deliberate; robots posting unsolicited essays on every PR are how civilizations decline.

## How it works

1. Parses a GitHub PR URL.
2. Fetches the PR diff from the GitHub API using the diff media type.
3. Sends the diff to Claude Code with a strict JSON schema.
4. Validates the structured response.
5. Renders Markdown suitable for a GitHub PR comment.

The diff is treated as untrusted data. Instructions embedded inside the diff are explicitly ignored.

## Sample output

See `sample-output-1.md` and `sample-output-2.md` for two real PR review examples produced by this tool:

- `sample-output-1.md`: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2459
- `sample-output-2.md`: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2457
