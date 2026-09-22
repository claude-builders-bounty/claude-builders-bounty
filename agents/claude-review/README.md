# claude-review — structured PR review agent

**Bounty:** [#4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) — $150

Takes a GitHub pull request (or a local unified diff), analyzes the change set, and emits a structured Markdown review with:

- Summary of changes (2–3 sentences)
- Identified risks (list)
- Improvement suggestions (list)
- Confidence score: `Low` / `Medium` / `High`

## Setup

```bash
# 1) Clone this folder (or the bounty fork branch)
git clone https://github.com/masaki12214/claude-builders-bounty.git
cd claude-builders-bounty && git checkout feat/claude-review-agent-masaki

# 2) Optional: Anthropic key for LLM-refined reviews
export ANTHROPIC_API_KEY=sk-ant-...   # omit for offline heuristic mode

# 3) Optional: GitHub token for private repos / higher rate limits
export GITHUB_TOKEN=ghp_...           # public PRs work unauthenticated
```

Requires: Python 3.9+ (stdlib only). Layout: `claude_review.py` + `lib/` (`github_io`, `heuristic`, `output`, `patterns`).

## Usage (CLI)

```bash
# Preferred entrypoint
./agents/claude-review/claude-review --pr https://github.com/owner/repo/pull/123

# Or via python
python3 agents/claude-review/claude_review.py --pr owner/repo#123

# Offline / CI with a saved patch
python3 agents/claude-review/claude_review.py --diff ./change.patch --title "My change"

# Machine-readable
python3 agents/claude-review/claude_review.py --pr URL --json
```

## Usage (GitHub Action)

Copy `agents/claude-review/.github/workflows/claude-review.yml` to your repo's `.github/workflows/`.

Optional repository secret: `ANTHROPIC_API_KEY` (without it the action still posts a heuristic review).

## Modes

| Mode | When | Behavior |
|------|------|----------|
| `heuristic` | default / no API key | Pattern + metadata analysis of the PR diff |
| `llm` | `ANTHROPIC_API_KEY` set | Same inputs refined by Claude; falls back to heuristic on failure |

## Sample outputs

Real PRs reviewed offline (heuristic) for this submission:

1. [`examples/review-claude-builders-4402.md`](./examples/review-claude-builders-4402.md) — docs/template PR
2. [`examples/review-express-7482.md`](./examples/review-express-7482.md) — dependency security bump

Regenerate:

```bash
python3 claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4402 --no-llm > examples/review-claude-builders-4402.md
python3 claude_review.py --pr https://github.com/expressjs/express/pull/7482 --no-llm > examples/review-express-7482.md
```

## Acceptance checklist

- [x] CLI: `claude-review --pr https://github.com/.../pull/N`
- [x] GitHub Action workflow YAML included
- [x] Structured Markdown: summary / risks / suggestions / confidence
- [x] Tested on ≥2 real GitHub PRs (samples above)
- [x] README with setup + usage
