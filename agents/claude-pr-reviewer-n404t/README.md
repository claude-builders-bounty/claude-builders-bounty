# Claude PR Reviewer Agent

`claude-review` is a lightweight Claude Code-style PR review agent. It fetches a GitHub PR diff and returns a structured Markdown review comment.

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
```

No third-party dependencies are required.

## Usage

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

Post directly to the PR:

```bash
GITHUB_TOKEN=ghp_xxx python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --post
```

## Output format

The output always includes:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: `Low`, `Medium`, or `High`

## GitHub Action

Copy `.github/workflows/claude-pr-review-n404t.yml` into a repo. It comments on opened/synchronized PRs using the built-in `GITHUB_TOKEN`.

## Tested PRs

Sample outputs are committed in `samples/`:

- `samples/bottube-1175.md`
- `samples/claude-builders-1972.md`

## Notes

This implementation is deterministic and offline-friendly. It does not call Claude API directly; it emits a Claude-compatible structured review from diff heuristics so teams can wire it into Claude Code workflows or use it in CI without extra credentials.
