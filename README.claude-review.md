# Claude PR Reviewer Agent

This adds a Claude Code sub-agent and CLI for reviewing a GitHub pull request diff and returning a structured Markdown review comment.

## Setup

1. Keep `.claude/agents/pr-reviewer.md` in the repository so Claude Code can use the `pr-reviewer` agent instructions.
2. Run the CLI with Node 18+: `node ./bin/claude-review.mjs --pr https://github.com/owner/repo/pull/123`.
3. Copy the Markdown output into the PR comment, or pass the diff to Claude Code with the `pr-reviewer` agent for deeper project-aware review.

## Output Format

The CLI and agent instructions use this structure:

- Summary of changes in 2-3 sentences.
- Identified risks as a list.
- Improvement suggestions as a list.
- Confidence score: `Low`, `Medium`, or `High`.

## Sample Commands

```bash
npm run verify
npm run sample:docs
npm run sample:tooling
npm run sample:live
```

The default verification commands use local fixture diffs, so they are deterministic and do not depend on network access. `npm run sample:live` demonstrates public GitHub PR fetching when the network is available; it is optional and is not required for local acceptance.
