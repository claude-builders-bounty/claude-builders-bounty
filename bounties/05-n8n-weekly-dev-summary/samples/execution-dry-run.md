# Offline dry-run validation (no secrets)

## Mock activity blob (same shape as Merge Activity node)

```json
{
  "repo": "claude-builders-bounty/claude-builders-bounty",
  "language": "EN",
  "window_start": "2026-07-04T00:00:00.000Z",
  "commits": [
    "feat: claude-review structured PR review agent (#4)",
    "feat: generate structured CHANGELOG from git history (#1)"
  ],
  "closed_issues": [],
  "merged_prs": ["#3363 PreToolUse hook", "#3364 CHANGELOG skill"],
  "counts": { "commits": 2, "issues": 0, "prs": 2 }
}
```

## Claude user message template

```
Write a weekly narrative engineering summary in language=EN (EN or FR).
Use only this JSON activity dump. Be concrete about themes, risk, and momentum.
```

## Expected Discord message shape

```
**Weekly summary — owner/repo**

<claude narrative paragraphs>
```

## Live test checklist

- [ ] Import JSON into n8n ≥1.50
- [ ] One manual execution with real PAT + Anthropic key
- [ ] Discord message received
- [ ] Screenshot `Executions` green row attached to PR comment
