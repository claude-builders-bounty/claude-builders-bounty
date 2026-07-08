# generate-changelog

Generate a structured `CHANGELOG.md` from git commit history.

## Setup (3 steps)

```bash
chmod +x changelog.sh
./changelog.sh
# Output: CHANGELOG.md
```

## Sample Output

```markdown
# Changelog

## [v1.2.0] - 2026-07-08

### Added
  - feat: add dark mode toggle
### Fixed
  - fix: resolve login redirect loop
  - fix: handle null user session
### Changed
  - refactor: extract auth middleware
  - chore: update dependencies
### Removed
  - drop: legacy v1 API endpoints
```

## How It Works

1. Finds latest git tag
2. Collects commits since that tag (max 50)
3. Categorizes by conventional commit prefixes:
   - `feat:` / `add:` → Added
   - `fix:` / `bug:` → Fixed
   - `refactor:` / `chore:` / etc → Changed
   - `remove:` / `drop:` → Removed
4. Outputs clean CHANGELOG.md
