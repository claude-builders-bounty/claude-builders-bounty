# PR Notes

Closes #4.

## What Changed

- Added `submissions/issue-4-pr-review-agent/claude-review`, a dependency-free Python CLI for structured PR review comments.
- Added `AGENT.md` with Claude Code sub-agent operating instructions.
- Added README setup and usage instructions.
- Added a small local test script and real public PR review samples.

## Acceptance Criteria

- CLI works with `./claude-review --pr https://github.com/owner/repo/pull/123`.
- Output includes summary, risks, suggestions, and confidence score.
- Tested against two public GitHub PRs; outputs are included under `samples/`.
- README setup and usage instructions are included.
