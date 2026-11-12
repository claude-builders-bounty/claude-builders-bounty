# claude-review — PR review sub-agent for Claude Code

A Claude Code sub-agent that takes a GitHub PR, fetches the diff, and returns a
structured Markdown review: summary, risks, suggestions, and a confidence score.

## Usage
```bash
claude-review --pr https://github.com/owner/repo/pull/123
claude-review --pr owner/repo#123
claude-review --repo owner/repo --pr 123
```

Requires `gh` CLI (authenticated) for private repos; public repos work without it.

## Output format
```markdown
# PR Review: owner/repo#N
## Summary
Changes N file(s), +A/-D lines. Files touched: ...
## Identified Risks
- ...
## Improvement Suggestions
- ...
## Confidence Score: High / Medium / Low
```

## How it works
1. Parses the PR reference into (owner, repo, number).
2. Fetches the diff via `gh pr diff` (private) or the public `.diff` URL (public).
3. Scans for risk patterns (destructive ops, shell injection, hardcoded secrets,
   unsafe SQL, swallowed exceptions) and improvement signals (missing tests,
   oversized PR, TODO markers, missing docs).
4. Emits a heuristic confidence score.

## Tested on real PRs
- `psf/requests#6500` → 1 file, +1/-1, no risks, **High** confidence
- `tiangolo/fastapi#10000` → 1 file, +14/-0, "no tests" suggestion, **High** confidence

## Install
```bash
cp claude-review.py ~/.claude/hooks/claude-review.py && chmod +x ~/.claude/hooks/claude-review.py
```
