# SKILL.md — Changelog Generator

## Description
Automatically generates a structured `CHANGELOG.md` from a project's git history.  
Works via `/generate-changelog` command in Claude Code, or run `python generate_changelog.py` directly.

## Usage

### In Claude Code
```
/generate-changelog
```

### CLI
```bash
python generate_changelog.py
```

## What It Does
1. Detects the latest git tag (or falls back to initial commit)
2. Fetches all commits since that tag
3. Auto-categorizes each commit into:
   - **Added** — new features (`feat:`, `add`, `new`, etc.)
   - **Fixed** — bug fixes (`fix:`, `bug`, `issue`, etc.)
   - **Changed** — refactoring, updates (`change:`, `update`, `refactor`, etc.)
   - **Removed** — deletions (`remove:`, `delete`, `deprecate`, etc.)
4. Generates a properly formatted `CHANGELOG.md` section
5. Prepends it to existing `CHANGELOG.md` (or creates a new one)

## Output Format
Follows [Keep a Changelog](https://keepachangelog.com/) convention:

```markdown
## [0.2.0] - 2026-05-17

### Added
- New feature X (abc1234)
- Add yyy support (def5678)

### Fixed
- Fix crash when loading config (ghi9012)

### Changed
- Refactor database layer (jkl3456)

### Removed
- Deprecate old API v1 (mno7890)
```

## Commit Categorization Rules

| Category | Conventional Commit Prefix | Keywords |
|----------|---------------------------|----------|
| Added | `feat:`, `feature:` | add, new, implement, introduce, create |
| Fixed | `fix:`, `bugfix:`, `hotfix:` | fix, bug, issue, resolve, patch |
| Changed | `change:`, `refactor:`, `improve:`, `perf:` | change, update, modify, refactor, improve, optimize |
| Removed | `remove:`, `delete:`, `deprecate:` | remove, delete, deprecate, drop |

## Requirements
- Python 3.8+
- Git repository with at least one commit
- (Optional) Git tags for versioning

## Notes
- If no tags exist, uses the initial commit as baseline
- Auto-increments patch version from latest tag (e.g., `0.1.0` → `0.1.1`)
- Each entry links to the commit on GitHub (update repo URL in script if needed)
