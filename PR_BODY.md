## Summary

Adds `claude-review`, a Python CLI for bounty #4 that reviews a GitHub PR diff and prints a structured Markdown review comment.

## What is included

- `claude_review.py` CLI
- URL parser for `https://github.com/owner/repo/pull/123`
- Public GitHub `.diff` fetching, no token required for public PRs
- Static diff heuristics for:
  - `shell=True`
  - hard-coded secrets/tokens/passwords/API keys
  - dynamic execution via `eval` / `exec`
  - destructive command or SQL patterns
  - missing test coverage signals
- Markdown output sections:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence score
- Unit tests
- Two real PR sample outputs in `samples/`

## Test plan

```bash
python3 -m unittest tests/test_claude_review.py -v
```

Result: 6 tests pass.

## Closes

Closes #4
