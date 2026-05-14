# PR Reviewer Agent

Claude Code sub-agent plus CLI for reviewing a GitHub pull request and producing
a structured Markdown review comment.

## Setup

Requires Node.js 20 or newer. Node.js 22 LTS is recommended.

```bash
cd agents/pr-reviewer
npm link
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

By default, the CLI uses `--engine auto`: it tries the bundled Claude Code
sub-agent first, then falls back to the deterministic local reviewer if Claude
Code is unavailable. To require Claude Code sub-agent mode, run:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --engine claude
```

To avoid Claude usage entirely, run:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --engine local
```

The Claude engine uses the project sub-agent at:

```text
.claude/agents/pr-reviewer.md
```

## Output Format

The command prints Markdown with:

- summary of changes in 2 to 3 sentences
- identified risks
- improvement suggestions
- confidence score: Low, Medium, or High

## GitHub Rate Limits

Public PRs can be fetched without authentication. For higher GitHub API limits,
set one of:

```bash
export GITHUB_TOKEN=your_token
export GH_TOKEN=your_token
```

Do not commit tokens.

If GitHub returns a rate-limit error, set `GITHUB_TOKEN` or `GH_TOKEN` and rerun
the command.

## Posting Comments

This tool returns a structured Markdown review comment. It does not post to
GitHub automatically, so reviewers can inspect the output before publishing it.

## Samples

Sample outputs from real GitHub PRs are in `samples/`:

- `samples/claude-builders-bounty-1359.md`
- `samples/claude-builders-bounty-1360.md`

They were generated with:

```bash
claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1359 --engine local
claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1360 --engine local
```

An additional Claude Code sub-agent sample is included at
`samples/claude-builders-bounty-1359-claude.md`.
