---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history using Conventional Commits. Use when a user asks to "write a changelog", "summarize what changed", "release notes", or before cutting a release/tag.
---

# Generate Structured CHANGELOG

Turn git history into a clean `CHANGELOG.md` grouped by change type.

## When to use
- User says "generate a changelog", "what changed since v1.0?", "make release notes".
- Before tagging a release.

## Script
`changelog.py` — pure stdlib, no deps, cross-platform.

## Usage
```bash
# All unreleased commits vs last tag
python3 changelog.py --repo . --output CHANGELOG.md

# Between two tags
python3 changelog.py --from-tag v0.9.0 --to-tag v1.0.0 --title "v1.0.0"

# Last 2 weeks
python3 changelog.py --since "2 weeks ago" --title "Recent"
```

## Output format
Keep-a-Changelog style, grouped into Added / Fixed / Changed / Docs / etc.
based on the Conventional Commit prefix (`feat:`, `fix:`, `docs:`, ...).

## Notes
- Commits are grouped by type; scope `(api)` is ignored for grouping.
- Merge commits are excluded.
- If no commits match, exits 1 with a clear message.
