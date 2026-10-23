---
name: generate-changelog
description: "Generate a structured CHANGELOG.md from git history, categorized into Added, Fixed, Changed, and Removed since the last tag."
---

# Generate Changelog Skill

Automatically inspects the local Git history since the last release tag (or repository inception) and builds a clean, structured `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/) standard.

## Triggers
- Command `/generate-changelog`
- Execution of `bash changelog.sh` or `python scripts/changelog.py`

## Instructions

1. Identify the latest git tag:
   ```bash
   git describe --tags --abbrev=0 2>/dev/null
   ```
   If no tag exists, inspect all commits on the current branch.

2. Fetch commit messages, hashes, and authors since that tag:
   ```bash
   git log <LAST_TAG>..HEAD --pretty=format:"%s (%h by %an)"
   ```

3. Categorize each commit according to Conventional Commits:
   - **Added**: `feat:`, `feature:`, `add:`, `new:`
   - **Fixed**: `fix:`, `bug:`, `patch:`, `hotfix:`
   - **Changed**: `refactor:`, `perf:`, `chore:`, `style:`, `update:`, `change:`
   - **Removed**: `revert:`, `deprecate:`, `remove:`, `drop:`

4. Format the output adhering to Markdown specifications:
   - Section heading with Version / Date: `## [Unreleased] - YYYY-MM-DD`
   - Subsections for each non-empty category (`### Added`, `### Fixed`, `### Changed`, `### Removed`).
   - Bullet points linking commit hashes.

5. Update or create `CHANGELOG.md` at the project root while preserving any previous release history.
