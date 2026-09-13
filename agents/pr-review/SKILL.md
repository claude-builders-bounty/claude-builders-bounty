---
name: pr-review
description: Review a GitHub pull request and emit structured Markdown (summary, risks, suggestions, confidence). Use when the user shares a PR URL or asks for a code review of a pull request.
---

# PR Review

Produce a structured Markdown review of a GitHub PR.

## Steps

1. Get the PR URL from the user (or infer from the current branch).
2. Run:

```bash
python3 agents/pr-review/claude_review.py --pr https://github.com/OWNER/REPO/pull/N
```

3. Show the Markdown output. Optionally write to a file with `--output review.md`.

## Output contract

Always include these four sections:

1. **Summary of changes** — 2–3 sentences
2. **Identified risks** — list (or "None detected")
3. **Improvement suggestions** — list
4. **Confidence score** — Low / Medium / High

## Confidence heuristic

- High: ≤5 files, <200 added lines, tests present or no risks
- Low: >25 files or >2000 added lines or ≥4 risk hits
- Medium: otherwise

## Notes

- Requires `gh` CLI (authenticated for private repos).
- Static scan is a first pass — call out anything that needs human judgment.
