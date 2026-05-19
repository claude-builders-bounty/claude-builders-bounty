# Generate Changelog

Generate a structured `CHANGELOG.md` from a project's git history.

## Usage

```
/generate-changelog
```

Or run directly:

```bash
bash skills/generate-changelog/changelog.sh
```

## What it does

1. Fetches all commits since the last git tag (or from the beginning if no tags exist)
2. Auto-categorizes commits into:
   - **Added** — New features (`feat:`, `feature:`, `add:`)
   - **Fixed** — Bug fixes (`fix:`, `bugfix:`, `hotfix:`)
   - **Changed** — Changes/refactors (`change:`, `refactor:`, `update:`, `chore:`)
   - **Removed** — Removals (`remove:`, `delete:`, `deprecate:`)
3. Outputs a properly formatted `CHANGELOG.md`

## Setup

1. Clone this repo and copy the `skills/generate-changelog/` directory into your project
2. Run `bash skills/generate-changelog/changelog.sh`
3. Review and commit the generated `CHANGELOG.md`

## Requirements

- Bash 4+
- Git
- No additional dependencies

## Example Output

```markdown
# Changelog

## [Unreleased]

### Added
- feat: add user authentication module (abc1234)
- add: dark mode support (def5678)

### Fixed
- fix: resolve login timeout on slow connections (ghi9012)

### Changed
- refactor: simplify database connection pool (jkl3456)

### Removed
- remove: deprecated legacy API endpoints (mno7890)
```
