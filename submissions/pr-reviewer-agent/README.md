# Claude PR Reviewer Agent

This submission implements bounty #4: a Claude Code sub-agent plus a `claude-review` CLI that reviews a GitHub pull request diff and returns a structured Markdown comment.

## What it returns

Every review uses these sections:

- `## Summary` - 2-3 sentence summary of the change.
- `## Identified risks` - concrete risks grounded in the diff.
- `## Improvement suggestions` - actionable follow-ups scoped to the visible diff.
- `## Confidence` - `Low`, `Medium`, or `High` with a reason.

## Setup

Install Claude Code and authenticate it:

```bash
npm install -g @anthropic-ai/claude-code
claude setup-token
```

The CLI runs Claude Code with `--bare` so the review is isolated from local `CLAUDE.md` files, hooks, plugins, and user-level project context. This keeps the review grounded in the supplied PR diff.

Install this CLI from the repository root:

```bash
npm install -g ./submissions/pr-reviewer-agent
```

## CLI usage

Review a public GitHub PR:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Write the review to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Review a saved diff:

```bash
claude-review --diff-file ./example.diff
```

For private repositories or higher GitHub API limits, set `GITHUB_TOKEN`.

## GitHub Action usage

Copy `workflows/claude-pr-review.yml` to `.github/workflows/claude-pr-review.yml`.

Add a repository secret named `CLAUDE_CODE_OAUTH_TOKEN`. The workflow installs Claude Code, runs `claude-review --pr <pull-request-url>`, and posts the generated Markdown as a PR comment.

The workflow uses the `pull_request` event and avoids checking out untrusted code for execution beyond installing this already-merged tool from the base branch.

## Agent definition

The reusable Claude Code sub-agent lives at:

```text
.claude/agents/pr-reviewer.md
```

The CLI passes the agent through Claude Code's `--agents` and `--agent pr-reviewer` options, so it works even when the caller has not copied the agent into their own project.

## Real PR test outputs

Generated on 2026-05-13 with Claude Code CLI `2.1.126`:

- `examples/pr-1209-output.md` reviews <https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1209>
- `examples/pr-1190-output.md` reviews <https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1190>

## Notes

- Large diffs are truncated at 180 KB by default and the agent is instructed to lower confidence when truncation occurs.
- `CLAUDE_REVIEW_MAX_DIFF_BYTES` or `--max-diff-bytes` can raise or lower that budget.
- `CLAUDE_REVIEW_CLAUDE_BIN` can point to a non-default Claude Code binary.
