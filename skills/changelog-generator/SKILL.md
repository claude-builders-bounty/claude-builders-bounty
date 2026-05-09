# SKILL.md — Structured CHANGELOG Generator

## Description
Generates a structured `CHANGELOG.md` from a project's git history.
Auto-categorizes commits into Added / Fixed / Changed / Removed sections.

## Usage
```bash
# Basic — generates changelog from last git tag to HEAD
bash changelog.sh

# Custom since point
bash changelog.sh --since v1.0.0

# Specific repo
bash changelog.sh --repo /path/to/project

# Custom output file
bash changelog.sh --output docs/CHANGELOG.md

# Verbose mode
bash changelog.sh --verbose
```

## Commit Convention (Conventional Commits)
The script auto-categorizes based on commit message prefixes:

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `feature:`, `implement:` | Added |
| `fix:`, `bug:`, `hotfix:`, `patch:` | Fixed |
| `chore:`, `refactor:`, `update:`, `improve:` | Changed |
| `remove:`, `delete:`, `deprecate:`, `drop:` | Removed |

## Output Format
```markdown
# Changelog

## [v1.2.0] - 2026-05-09

### Added
- **Alice**: Implement user profile page
- **Bob**: Add dark mode toggle

### Fixed
- **Carol**: Fix pagination overflow on mobile

### Changed
- **David**: Update dependencies to latest versions
```

## Sample Output
See `sample/CHANGELOG.md` for a full example generated from a real repository.
