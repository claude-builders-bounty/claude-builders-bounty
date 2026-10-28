---
name: generate-changelog
description: Automatically generates a structured, Keep-a-Changelog compliant CHANGELOG.md from git commit history since the latest release tag.
---

# Generate Changelog Skill

This skill inspects the repository's git commit log since the latest git tag (or from initial commit if untagged), parses Conventional Commits and standard commit messages, and formats them into a clean, human-readable `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standard.

## When to Use
- When releasing a new version or preparing release notes.
- When summarizing recent changes for team updates or open-source documentation.
- When running the slash command `/generate-changelog`.

## Categories Mapped
Commits are parsed and sorted into standard categories:
- **Added**: New features, endpoints, components (`feat:`, `add:`, `new:`)
- **Fixed**: Bug fixes, crash resolutions, patch updates (`fix:`, `bug:`, `patch:`)
- **Changed**: Refactoring, enhancements, optimizations (`refactor:`, `perf:`, `change:`, `update:`, `style:`)
- **Removed**: Deprecated features, cleanups, removed code (`remove:`, `deprecate:`, `delete:`)
- **Maintenance / Internal**: CI/CD, docs, build tooling (`chore:`, `docs:`, `ci:`, `test:`, `build:`)

## Execution Workflow
When the user requests a changelog:
1. Identify the latest git tag: `git describe --tags --abbrev=0 2>/dev/null`
2. If a tag is found, query commits in range: `git log <latest_tag>..HEAD --pretty=format:"%h|%s|%an|%ad" --date=short`
3. If no tag exists, query recent commits: `git log -n 50 --pretty=format:"%h|%s|%an|%ad" --date=short`
4. Alternatively, execute the bundled script:
   ```bash
   bash skills/generate-changelog/changelog.sh
   # or
   python3 skills/generate-changelog/generate_changelog.py --output CHANGELOG.md
   ```
5. Output the result formatted under `## [Unreleased]` or `## [vX.Y.Z] - YYYY-MM-DD`.
