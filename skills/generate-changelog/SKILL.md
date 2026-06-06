---
name: generate-changelog
description: Analyzes git history using conventional commits and generates a structured changelog in markdown
trigger: when the user asks to generate changelog, create release notes, or what changed
---

# Generate Changelog

Generate a structured changelog from a git repository's conventional commit history.

## Steps

1. Run: `git log --oneline --no-decorate $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD`
2. Parse commits into categories by conventional commit type
3. Output formatted markdown with dates
