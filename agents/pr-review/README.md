# claude-review — structured PR review agent

Opire bounty **#4** ($150). Produces a Markdown review with:

- Summary of changes (2–3 sentences)
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

## Setup (3 steps)

1. Clone this repo (or copy `agents/pr-review/`).
2. Ensure `gh` is authenticated (`gh auth status`) **or** pass a unified `--diff` file.
3. Optional: export `ANTHROPIC_API_KEY` for Claude narrative polish (heuristic engine always runs).

## CLI usage

```bash
# Review a live GitHub PR
python3 agents/pr-review/claude_review.py --pr https://github.com/owner/repo/pull/123

# Or via wrapper
./agents/pr-review/claude-review --pr https://github.com/owner/repo/pull/123 -o review.md

# Offline diff
python3 agents/pr-review/claude_review.py --diff ./my.patch --title "feat: demo"
```

## GitHub Action

Workflow template: `agents/pr-review/github-action.claude-pr-review.yml` (copy to `.github/workflows/`).

- Triggers on `pull_request` and `workflow_dispatch`
- Posts the structured Markdown as a PR comment (when permissions allow)
- Optional secret `ANTHROPIC_API_KEY` upgrades summary quality

## Samples

See `samples/pr-review/` for real PR outputs generated during testing.
