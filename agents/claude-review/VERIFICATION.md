# Verification — claude-review (Bounty #4)

Generated 2026-09-22 ~03:51 Asia/Taipei during overnight earn patrol.

## Commands run (stdlib / no API key)

```bash
cd agents/claude-review
python3 claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4402 --no-llm
python3 claude_review.py --pr https://github.com/expressjs/express/pull/7482 --no-llm
python3 claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4403 --no-llm --json | head
```

## Acceptance map

| Criterion | Evidence |
|-----------|----------|
| CLI `claude-review --pr URL` | `claude-review` wrapper + `claude_review.py` |
| GitHub Action YAML | `.github/workflows/claude-review.yml` + nested copy under agent |
| Structured Markdown (summary / risks / suggestions / confidence) | `lib/output.py` `render_markdown` + `examples/*.md` |
| Tested on ≥2 real PRs | `examples/review-claude-builders-4402.md`, `examples/review-express-7482.md` |
| README ≤ setup steps | `README.md` |

## Notes

- Heuristic mode works without `ANTHROPIC_API_KEY` (offline CI-friendly).
- LLM refine is optional and falls back on failure.
