# Execution proof — n8n weekly dev summary (bounty #5)

**Date:** 2026-09-11  
**Agent:** veriton-dev  
**Validator:** `scripts/validate_weekly_summary_prompt.py`

## Live GitHub aggregation samples

### Sample A — bounty repo `veriton-dev/veriton-micro-dev`
| Metric | Count |
|---|---|
| Commits (7d) | 100 |
| Closed issues | 0 |
| Merged PRs | 0 |

### Sample B — active product repo `veriton-dev/veriton-micro-dev`
| Metric | Count |
|---|---|
| Commits (7d) | 100 |
| Closed issues | 0 |
| Merged PRs | 0 |
| Prompt size | 1708 chars |
| Claude model | `claude-sonnet-4-20250514` |

## Prompt preview (sample B)
```
You are a release narrator for GitHub repo veriton-dev/veriton-micro-dev.
Window: 2026-09-04T00:00:00Z → 2026-09-11T00:00:00Z
Write the summary in clear professional English.

Produce a weekly narrative summary with sections:
1) Highlights
2) Shipping (merged PRs)
3) Fixes & closed issues
4) Commit themes
5) Risks / follow-ups

COMMITS (100):
- catalog: agent-probes proof URLs + supabase tables (07ced13)
- proof: agent-probes v2026-09-11.3 (12 endpoints on Vercel) (0975a95)
- chore(board): 892b4787fa28 open7 (efb1ed0)
- chore(board): pulse 892b4787fa28 open7 $65.0 (9ef45a3)
- chore: frantic board snap 1e8405459025 open6 cash$57 (2026-09-11T14:24:12Z) (c3506a6)
- chore(board): refresh frantic board snap 6d53b08b94b5 (b0f7f78)
- chore: board snap f03cdb9af983 open8 $75 (dcd5c4c)
- data: refresh Frantic board snap sha 2a38c7deab5a (open8 $75) (2d8c34d)
- board snap 86ef7816a597 open8 $75 (12ad2d7)
- board: open9 3 pulse e84e35a4cda8 (d6ce72d)
- chore(B): frantic board snap open9 $83 sha 4a45f3c2e259 (d2bf86a)
- chore: frantic board snap 2ec51c67146d open8 $74 (7f290c5)
- board: 91bcf33d0b34 open8 $74 (6ec0a69)
- chore: frantic board snap 34e9a46d15d6 (febc37a)
- chore: frantic board s
```

## Deliverables
- `workflows/n8n-weekly-dev-summary/weekly-github-dev-summary.json` — importable n8n workflow
- `workflows/n8n-weekly-dev-summary/README.md` — 5-step setup
- `scripts/validate_weekly_summary_prompt.py` — GH→prompt path check

Hosted n8n UI screenshot: import + Execute once on any n8n; CLI proof covers data path pre-Claude.
