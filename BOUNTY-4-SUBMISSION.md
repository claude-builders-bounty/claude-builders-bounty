# Bounty Submission Notes

Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4

## Proposed PR Summary

Implements a `claude-review` CLI that accepts a GitHub PR URL, fetches the diff, and returns a structured Markdown review comment with the required sections: summary, identified risks, improvement suggestions, and confidence score. The tool can run fully offline against a local diff, uses a deterministic heuristic reviewer by default, and optionally delegates review generation to Claude CLI when available.

## Acceptance Checklist

- [x] CLI usage: `claude-review --pr https://github.com/owner/repo/pull/123`
- [x] GitHub Action workflow included
- [x] Claude Code project subagent included at `.claude/agents/pr-reviewer.md`
- [x] Structured Markdown output
- [x] Summary of changes
- [x] Identified risks
- [x] Improvement suggestions
- [x] Confidence score: Low / Medium / High
- [x] README with setup and usage
- [x] Unit tests
- [x] Two real PR sample outputs

## Suggested PR Body

```markdown
Closes #4.

## What changed

- Adds `claude-review`, a Python CLI that reviews a GitHub PR diff and emits the required structured Markdown comment.
- Adds a Claude Code project subagent at `.claude/agents/pr-reviewer.md` that delegates to the CLI.
- Adds optional `--post-comment` support using `GITHUB_TOKEN`.
- Adds a manual GitHub Action workflow that can generate a review artifact or post the comment.
- Adds unit tests and sample outputs from two real public PRs.

## Validation

- `python -m unittest discover -s tests`
- `claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2827 --output samples/claude-builders-2827.md`
- `claude-review --pr https://github.com/python/cpython/pull/151541 --output samples/cpython-151541.md`
```

## Claim Step Still Required

Before opening the PR, comment `/opire try` on the issue from the user's GitHub account. That is an account-sensitive action and should be done only with explicit action-time approval.
