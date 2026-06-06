# Claude Review Agent

`claude-review` is a dependency-free Claude Code PR review agent for bounty #4.

## Setup

1. Run with Node 20 or newer.
2. Optionally set `GITHUB_TOKEN` for higher API limits.
3. Review a PR:

```bash
node bin/claude-review.mjs --pr https://github.com/owner/repo/pull/123
```

## Output

The CLI returns structured Markdown with:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score

## GitHub Action

`examples/github-actions/claude-review.yml` is an optional workflow users can copy into `.github/workflows/`. It comments the generated review on new or updated PRs and uses the built-in `GITHUB_TOKEN` with read content and write pull request permissions.

## Claude Code Sub-Agent

The reusable sub-agent definition lives at `.claude/agents/pr-reviewer.md`. It tells Claude Code to run the CLI, then tighten the comment so the final review stays grounded in the diff.

## Verification

```bash
npm test
node bin/claude-review.mjs --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2506
node bin/claude-review.mjs --pr https://github.com/Opire/docs/pull/10
```

The generated outputs for those two real pull requests are committed in `samples/`.
