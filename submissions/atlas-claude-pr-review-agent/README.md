# Claude PR Review Agent - Local Prototype

This is a local, no-credential prototype for the bounty:

https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4

It does not comment on GitHub, open pull requests, claim the bounty, use Opire, store credentials, or contact third parties.

## Usage

```powershell
node bin\claude-review.mjs --pr https://github.com/owner/repo/pull/123
```

Write output to a file:

```powershell
node bin\claude-review.mjs --pr https://github.com/owner/repo/pull/123 --out review.md
```

Output:

- Summary of changes.
- Identified risks.
- Improvement suggestions.
- Changed files.
- Confidence score.

## Examples

```powershell
node bin\claude-review.mjs --pr https://github.com/geobrowser/geogenesis/pull/2422 --out examples/geogenesis-2422.md
node bin\claude-review.mjs --pr https://github.com/prisma/deployment-example-vercel/pull/211 --out examples/prisma-211.md
```

## Current Limits

- Uses only public GitHub API reads.
- No token support.
- Reviews are heuristic, not final maintainer-grade analysis.
- Large PRs may be summarized from the first 100 changed files.

## GitHub Action Example

See `.github/workflows/claude-review.yml` for a draft workflow that runs the CLI on pull requests. It is included as a local example only and has not been pushed anywhere.

## Claude Code Subagent

This package includes a Claude Code subagent definition:

```text
.claude/agents/pr-reviewer.md
```

The subagent file uses YAML frontmatter with `name`, `description`, `tools`, and `model`, followed by review instructions and the required Markdown output structure.

## External Actions That Require Felipe

- Commenting `/opire try`.
- Opening a PR.
- Submitting this prototype to the bounty repository.
- Configuring payout.
- Using a GitHub account or token.
