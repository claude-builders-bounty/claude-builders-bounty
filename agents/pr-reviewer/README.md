# PR Reviewer Agent — Bounty #4 ($150)

Claude Code sub-agent that reviews a GitHub PR and outputs structured Markdown.

## Setup

```bash
chmod +x agents/pr-reviewer/claude-review   # optional wrapper
```

Requires Python 3.10+. No API key needed for public PRs (uses GitHub REST + diff).

## Usage

```bash
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
python agents/pr-reviewer/claude_review.py --pr URL -o review.md
./agents/pr-reviewer/claude-review --pr URL
```

## GitHub Action

Copy `agents/pr-reviewer/.github/workflows/pr-review.yml` to your repo's `.github/workflows/`.

## Sample outputs

Real reviews included in `samples/`:

- `review-pr-2953.md` — destructive-command hook PR
- `review-pr-2954.md` — CLAUDE.md template PR

Regenerate:

```bash
python agents/pr-reviewer/claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2953 -o samples/review-pr-2953.md
python agents/pr-reviewer/claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2954 -o samples/review-pr-2954.md
```
