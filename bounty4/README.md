# Claude PR Review Agent (Opire bounty #4 — $150)

Structured Markdown PR reviews via CLI or GitHub Action.

## Setup (≤3 steps)

```bash
# 1) enter folder
cd bounty4

# 2) make CLI available (optional)
chmod +x claude-review
export PATH="$PWD:$PATH"

# 3) review a PR (requires gh auth OR GH_TOKEN)
claude-review --pr https://github.com/owner/repo/pull/123
# or: python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

Offline / fixture mode:

```bash
python3 claude_review.py --diff path/to.patch --title "feat: example"
```

## Output sections

- **Summary** — 2–3 sentences
- **Risks** — bullet list
- **Suggestions** — bullet list
- **Confidence** — Low / Medium / High

## Modes

| Mode | When |
|------|------|
| `heuristic` (default) | Deterministic static analysis of the unified diff — **no API key required** |
| `heuristic+llm` | If `ANTHROPIC_API_KEY` is set, optionally polishes the review via Claude |

Set `--no-llm` to force heuristic-only.

## GitHub Action

See `.github/workflows/claude-review.yml`. On `pull_request`, posts a structured review comment.

Required secrets for LLM polish: `ANTHROPIC_API_KEY` (optional). `GITHUB_TOKEN` is provided by Actions.

## Tests

```bash
python3 tests/test_claude_review.py
```

## Sample outputs

- `examples/review-pr-3672.md` — review of hook PR #3672
- `examples/review-pr-3673.md` — review of changelog PR #3673

## Notes

- Heuristic mode flags secrets, dangerous APIs, missing tests, oversized diffs.
- It is **not** a full semantic proof of correctness — Confidence reflects static signal strength.
