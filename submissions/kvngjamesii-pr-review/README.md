# claude-review — structured PR review agent

**Bounty:** [#4 — $150](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)  
**Author:** KvngJamesII

Claude Code–friendly agent that fetches a GitHub PR diff and emits a structured Markdown review:

- Summary (2–3 sentences)
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

Works **offline-heuristic** (no API key) or with **Anthropic Claude** when `ANTHROPIC_API_KEY` is set.

## Setup (CLI)

```bash
# 1) from this folder
chmod +x bin/claude-review
export GITHUB_TOKEN=$(gh auth token)   # optional but recommended for private/rate limits

# 2) review any public PR
./bin/claude-review --pr https://github.com/cli/cli/pull/10000

# 3) optional: Claude-backed review
export ANTHROPIC_API_KEY=sk-ant-...
./bin/claude-review --pr https://github.com/owner/repo/pull/123 --out review.md
```

## Setup (GitHub Action)

Copy `.github/workflows/claude-review.yml` into your repo. Optionally add repo secret `ANTHROPIC_API_KEY`. On every PR, the workflow posts a structured review comment.

## Sample outputs

See `samples/` — generated against two real public PRs (heuristic mode, reproducible without secrets).

## Design notes (why this is distinct)

- Dual mode: deterministic heuristic scanner **plus** optional Claude API — CI-friendly without keys
- Secret / XSS / SQL / `rm -rf` / force-push pattern library with confidence scoring
- Single-file Python 3.10+ stdlib only (no pip deps)
- Action posts the same Markdown schema as the CLI
