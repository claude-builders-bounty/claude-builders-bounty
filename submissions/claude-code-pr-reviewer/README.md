# 🤖 claude-review — AI-Powered PR Review Agent

> An agent that reviews GitHub PRs using Claude API and returns structured Markdown feedback.

**Bounty:** [claude-builders-bounty/claude-builders-bounty#4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) — $150 powered by Opire

---

## Quick Start

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."

bash claude-review.sh --pr https://github.com/owner/repo/pull/123
```

## Output Format

```
═══════════════════════════════════════════
  PR REVIEW — owner/repo#123
  PR Title Here
═══════════════════════════════════════════

## Summary of Changes
(2–3 sentence summary)

## Identified Risks
- Risk 1
- Risk 2

## Improvement Suggestions
- Suggestion 1
- Suggestion 2

## Confidence Score
**High / Medium / Low**

═══════════════════════════════════════════
```

## GitHub Action Setup

1. Add this workflow to `.github/workflows/claude-review.yml`
2. Set repository secrets:
   - `ANTHROPIC_API_KEY` — from https://console.anthropic.com
   - `GITHUB_TOKEN` — auto-provided (needs `pull-requests: write`)
3. PRs will be reviewed automatically on open/sync

## Requirements

- Bash 4+
- `curl`, `python3`
- Anthropic API Key (Claude Sonnet 4)
- GitHub Token (`repo` scope for private, `public_repo` for public)

## Sample Outputs

See [`sample-outputs/`](sample-outputs/) for real PR reviews:

| PR | Repo |
|----|------|
| [#30123](https://github.com/facebook/react/pull/30123) | facebook/react |
| [#69102](https://github.com/vercel/next.js/pull/69102) | vercel/next.js |

## Files

| File | Description |
|------|-------------|
| `claude-review.sh` | CLI review script |
| `.github/workflows/claude-review.yml` | GitHub Action workflow |
| `sample-outputs/` | Test outputs from real PRs |
| `README.md` | This guide |
