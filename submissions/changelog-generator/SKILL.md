# Generate structured CHANGELOG from git history

You are a changelog generator. When the user runs `/generate-changelog`, execute `bash changelog.sh` in the project root.

## What you do

1. Run `bash changelog.sh` (or `bash CHANGELOG.md` if already exists)
2. The script will:
   - Fetch commits since the last git tag
   - Auto-categorize into: **Added**, **Fixed**, **Changed**, **Removed**
   - Output a properly formatted CHANGELOG.md
3. If the project already has a CHANGELOG.md, prepend the new version section

## Output format

```markdown
# Changelog

## [v1.2.0] - 2026-05-18

### Added
- feat: add user authentication system
- feat: implement dark mode toggle

### Fixed
- fix: resolve login timeout on slow connections

### Changed
- refactor: migrate API calls to use async/await

### Removed
- remove: drop deprecated /v1/ endpoint
```

## Commit categorization rules

- Commits starting with `feat:` or `add:` → **Added**
- Commits starting with `fix:` or `bug:` → **Fixed**
- Commits starting with `refactor:`, `perf:`, `style:`, `docs:` → **Changed**
- Commits starting with `remove:`, `drop:`, `revert:` → **Removed**
- Everything else → **Changed**

## Rules

- Always use UTC dates
- Version number: if there's a git tag, use it; otherwise use "Unreleased"
- If no commits found since last tag, say "No changes since last release"
- Keep it concise — one line per commit
