---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag. Categorizes commits into Added, Fixed, Changed, and Removed sections. Use /generate-changelog to invoke.
---

# Generate CHANGELOG from Git History

Automatically generates a structured `CHANGELOG.md` from the project's git commit history since the last git tag.

## Usage

From any git repository:
```bash
bash generate-changelog.sh
```

Or within Claude Code:
```
/generate-changelog
```

## How It Works

1. Finds the most recent git tag (`git describe --tags --abbrev=0`)
2. Collects all commits since that tag
3. Categorizes commits based on Conventional Commits prefixes and keywords:
   - **Added** — `feat:`, `add:`, `Added`, `new`
   - **Fixed** — `fix:`, `bug:`, `Fixed`, `patch`, `resolve`
   - **Changed** — `refactor:`, `update:`, `Changed`, `tweak`, `improve`
   - **Removed** — `remove:`, `drop:`, `Removed`, `delete`, `deprecate`
4. Outputs a well-formatted `CHANGELOG.md` with version header, date, and categorized entries

## Output Format

```markdown
# Changelog

## [v1.2.0] - 2026-06-01

### Added
- Add user authentication module (#42)
- Add dark mode toggle (#45)

### Fixed
- Fix login redirect loop (#41)
- Fix mobile layout overflow (#43)

### Changed
- Update dependencies to latest versions
- Refactor database connection pool

### Removed
- Remove deprecated v1 API endpoints
```
