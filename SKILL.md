# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from git history.

## Trigger

User says `/generate-changelog` or asks to generate a changelog from git history.

## Execution

Run the included script:

```bash
python3 generate_changelog.py
```

## What It Does

1. Finds the most recent git tag via `git describe --tags --abbrev=0`
2. Gathers all commits since that tag (or all commits if no tag exists)
3. Categorizes each commit into one of four buckets:
   - **Added** — new features (`feat:`, `add:`, `new:`, implements, introduces)
   - **Fixed** — bug fixes (`fix:`, `bug:`, `hotfix:`, resolves, patches)
   - **Changed** — modifications (`refactor:`, `update:`, `improve:`, `chore:`)
   - **Removed** — deletions (`remove:`, `delete:`, `drop:`, deprecates)
4. Writes a properly formatted `CHANGELOG.md` with version header and date

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.3] - 2026-05-23

### Added
- feat: add dark mode toggle (abc1234)

### Fixed
- fix: correct navbar overflow on mobile (def5678)

### Changed
- refactor: extract API client into shared module (ghi9012)

### Removed
- remove: deprecated legacy auth endpoint (jkl3456)
```

## Notes

- Zero external dependencies beyond Python 3 standard library
- Works on any git repository
- Falls back gracefully when no tags exist (uses `Unreleased` as version)
