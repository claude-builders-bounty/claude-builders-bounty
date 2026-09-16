# Submission Draft

This is a local draft only. Do not post without Felipe's explicit approval.

## Bounty

https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4

## Draft comment

I prepared a local prototype for the PR review agent.

What it includes:

- CLI command: `node bin/claude-review.mjs --pr https://github.com/owner/repo/pull/123`
- Optional `--out review.md`
- Structured Markdown output:
  - summary;
  - identified risks;
  - improvement suggestions;
  - changed files;
  - confidence score.
- GitHub Actions workflow draft.
- Claude Code subagent definition at `.claude/agents/pr-reviewer.md`.
- Subagent compatibility notes at `docs/claude-code-subagent.md`.
- Two example outputs from public PRs.

I can open a PR with the implementation and examples if this direction fits the bounty.

## External action checklist

Before posting anything:

- Felipe approves GitHub account use.
- Felipe approves `/opire try` or alternative claim step.
- Felipe approves opening a PR.
- Payment/receiving method remains unset until needed.
