---
name: generate-changelog
description: Automatically inspects git commit history since the last tag and compiles a structured CHANGELOG.md categorized into Added, Fixed, Changed, and Removed.
---

# Git Changelog Generator Skill

Automatically extract git commits, parse Conventional Commits, group them by standard Keep a Changelog categories, and produce a clean `CHANGELOG.md`.

## When to Use
- Before cutting a new release or tagging a version.
- When summarizing recent contributions or preparing release notes.
- Command triggers: `/generate-changelog`, "generate changelog", "summarize release commits".

## Execution Workflow
1. Detect the most recent Git tag (`git describe --tags --abbrev=0`).
2. Collect all commits from that tag to `HEAD` (or all commits if no tag exists).
3. Classify commits into 4 semantic buckets:
   - **Added**: `feat:`, `add:`, `new:`
   - **Fixed**: `fix:`, `bugfix:`, `patch:`
   - **Changed**: `refactor:`, `chore:`, `perf:`, `docs:`, `update:`
   - **Removed**: `remove:`, `deprecated:`, `drop:`
4. Format the output with markdown links to commit hashes and author credits.
5. Write/update `CHANGELOG.md` at project root.

## CLI Usage
```bash
# Run via bash
bash changelog.sh

# Or run via Python directly
python generate_changelog.py