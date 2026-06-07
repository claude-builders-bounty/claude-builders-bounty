# Claude Review Agent

This package implements bounty issue #4:

https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4

It provides a deterministic Claude Code-style PR review agent that accepts a GitHub PR URL, reads public PR metadata and diff content, and returns a structured Markdown review comment.

It includes:

- A `claude-review` CLI.
- A project-level Claude Code sub-agent definition in `.claude/agents/claude-pr-reviewer.md`.
- A GitHub Action example in `examples/github-action.yml`.
- Sample outputs from two real GitHub PRs.

## Install

```bash
cd claude-review-agent
npm install
npm link
```

Node.js 18 or newer is required. No API key is required for public PRs. If GitHub API rate limits are low, set `GITHUB_TOKEN` in the environment.

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Or without linking:

```bash
npm run review -- --pr https://github.com/owner/repo/pull/123
```

Write the review to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --out review.md
```

## Claude Code sub-agent

The sub-agent definition lives at:

```text
.claude/agents/claude-pr-reviewer.md
```

Claude Code loads project sub-agents from `.claude/agents/`. The agent delegates PR URL review tasks to the local CLI and preserves the required Markdown sections.

## GitHub Action example

The workflow example lives at:

```text
examples/github-action.yml
```

It generates a review for the pull request that triggered the workflow and posts the Markdown as a PR comment using `gh pr comment`.

## Output format

The CLI prints Markdown with:

- Summary of changes, 2-3 sentences.
- Identified risks, as a list.
- Improvement suggestions, as a list.
- Confidence score: Low, Medium, or High.

## Sample verification

Generate two real-PR sample outputs:

```bash
npm run sample:react
npm run sample:node
```

Generated samples:

- `samples/react-32781.md`
- `samples/node-58362.md`

Validate the generated Markdown structure:

```bash
npm test
```

See `PROOF.md` for the acceptance-criteria mapping.

## How the agent works

1. Parses `https://github.com/owner/repo/pull/123`.
2. Fetches PR metadata from the GitHub REST API.
3. Fetches the PR diff.
4. Parses changed files, additions, deletions, test/docs/dependency changes, and risk-sensitive added lines.
5. Emits a compact Markdown review suitable for a PR comment.

## Notes

- The agent does not post comments by itself.
- The agent does not read private repositories unless the caller supplies a valid `GITHUB_TOKEN`.
- The review is heuristic and should be treated as a triage comment, not a replacement for maintainer review.
