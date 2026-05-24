# /generate-changelog

Generate a structured CHANGELOG.md from the project's git history.

## Usage

```
/generate-changelog
```

## What It Does

1. Finds the most recent git tag in the repository
2. Fetches all commits since that tag (or the last 30 commits if no tags exist)
3. Parses conventional commit messages (feat:, fix:, docs:, refactor:, etc.)
4. Categorizes commits into sections:
 - **Added** — `feat:`, `feature:` commits
 - **Fixed** — `fix:`, `bugfix:` commits
 - **Changed** — `docs:`, `refactor:`, `perf:`, `test:`, `chore:`, `style:` commits
 - **Removed** — `remove:`, `delete:`, `deprecate:`, `BREAKING CHANGE:` commits
5. Outputs a properly formatted `CHANGELOG.md`

## Arguments

- `since_tag` (optional) — Override the auto-detected tag to start from

## Example Output

```markdown
# Changelog

## [Unreleased] (2026-05-24)

### Added
- feat: add user authentication module

### Fixed
- fix: resolve login redirect loop

### Changed
- docs: update API documentation

### Removed
- remove: deprecated v1 endpoints
```

## Conventional Commit Prefixes

| Prefix | Category |
|--------|----------|
| feat, feature | Added |
| fix, bugfix | Fixed |
| docs, refactor, perf, test, chore, style | Changed |
| remove, delete, deprecate, BREAKING CHANGE | Removed |

Unprefixed commits are placed in an "Other Changes" section.
