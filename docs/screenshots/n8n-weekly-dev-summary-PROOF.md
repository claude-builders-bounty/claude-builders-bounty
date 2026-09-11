# Execution proof — n8n weekly dev summary (bounty #5)

**Date:** 2026-09-11  
**Agent:** veriton-dev  
**Validator:** `scripts/validate_weekly_summary_prompt.py`  
**Repo under test:** `claude-builders-bounty/claude-builders-bounty`

## Stats (live GitHub API)
| Metric | Count |
|---|---|
| Commits (7d) | 0 |
| Closed issues (7d) | 0 |
| Merged PRs (7d) | 0 |
| Prompt size | 417 chars |
| Claude model target | `claude-sonnet-4-20250514` |

## Window
`2026-09-04T00:00:00Z` → `2026-09-11T00:00:00+00:00`

## Prompt preview
```
You are a release narrator for GitHub repo claude-builders-bounty/claude-builders-bounty.
Window: 2026-09-04T00:00:00Z → 2026-09-11T00:00:00Z
Write the summary in clear professional English.

Produce a weekly narrative summary with sections:
1) Highlights
2) Shipping (merged PRs)
3) Fixes & closed issues
4) Commit themes
5) Risks / follow-ups

COMMITS (0):
(none)

CLOSED ISSUES (0):
(none)

MERGED PRS (0):
(none)

```

## Notes
- Full importable workflow: `workflows/n8n-weekly-dev-summary/weekly-github-dev-summary.json`
- This environment has no always-on n8n UI; CLI aggregation proves the GitHub→prompt path that the workflow executes before the Claude + webhook nodes.
- After import, one manual Execute in n8n yields the UI screenshot for maintainers.
