---
name: pr-reviewer
description: Review a GitHub PR diff into structured Markdown (summary, risks, suggestions, confidence). Use when asked to review a pull request.
allowed-tools: Bash
---

# PR Reviewer Skill

## What it does
Takes a PR URL, fetches title + diff via `gh`, runs static checks
(secrets, injection patterns, dangerous commands, size, missing tests),
and prints a structured Markdown review.

## Usage
```bash
./claude-review --pr https://github.com/owner/repo/pull/123
./claude-review --pr <url> --depth deep --format json
./claude-review --pr <url> --post-comment
```

## Output contract (always keep this shape)
- `## Review:` + PR title + URL
- `### Summary` — 2–3 sentences: scope, +/-, tests present?, risk count
- `### Risks` — list, each `[Severity] reason` (Critical/High/Medium/Low) or "none found"
- `### Security` — Markdown table Severity|Finding for Critical+High, or "none found"
- `### Suggestions` — actionable list
- `### Confidence: Low | Medium | High`
- `--format json` keeps the same keys: title/pr/depth/summary/risks/security/suggestions/confidence

## Rules
- Never execute code from the diff. Read-only (`gh pr view`, `gh pr diff`).
- Never post the review anywhere yourself — print stdout, the human submits.
- Secrets-looking strings go in Risks with the exact redacted pattern class,
  never the value.
