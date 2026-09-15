---
name: generate-changelog
description: Automatically generates or updates a structured CHANGELOG.md from git commits since the last tag.
---

# Generate Changelog Skill

This skill analyzes the project's git commit history since the most recent git tag and produces a clean, categorized `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standard.

## When to Use
- When preparing a new release or tag
- When running `/generate-changelog`
- When documenting changes made in a sprint or branch

## Execution Steps

1. **Identify Commit Range**:
   - Check if any git tags exist: `git describe --tags --abbrev=0`.
   - If tags exist, inspect commits from that tag to HEAD (`<tag>..HEAD`).
   - If no tags exist, inspect all repository commits.

2. **Categorize Commits**:
   - **`Added`**: Features and additions (`feat:`, `add:`, `new:`)
   - **`Fixed`**: Bug fixes and patches (`fix:`, `bug:`, `patch:`, `resolve:`)
   - **`Changed`**: Refactors, maintenance, docs, and style updates (`refactor:`, `perf:`, `chore:`, `docs:`, `style:`)
   - **`Removed`**: Deprecations and removals (`remove:`, `deprecate:`, `delete:`)

3. **Format & Write**:
   - Run the included script:
     ```bash
     python3 scripts/generate_changelog.py CHANGELOG.md
     # or on bash environments:
     bash scripts/changelog.sh CHANGELOG.md
     ```
   - Prepend the new release section directly beneath the main `# Changelog` header.
   - Display a summary of the categorized changes to the user.
