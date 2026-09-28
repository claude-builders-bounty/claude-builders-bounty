# Claude Code PR Reviewer Sub-Agent

A claude-review CLI that downloads a GitHub PR diff and returns a structured
Markdown review (Summary, Risks, Suggestions, Confidence score).

## Usage
`ash
export GITHUB_TOKEN=ghp_xxx
python claude-review.py --pr https://github.com/owner/repo/pull/123
`

## Output format
- **Summary of changes** (2-3 sentences)
- **Risks** (list)
- **Improvement suggestions** (list)
- **Confidence score: Low / Medium / High**

## Verified
Tested against 2 real GitHub PRs:
- semaphore-protocol/boilerplate PR #85 (+916/-12, 4 files)
- semaphore-protocol/boilerplate PR #88 (docs chore)
See outputs in the PR description.
