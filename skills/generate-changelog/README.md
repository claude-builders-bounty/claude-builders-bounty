# Structured CHANGELOG Generator

Generate clean, standardized `CHANGELOG.md` directly from git history in 3 steps.

## Quick Setup in 3 Steps
1. **Clone or copy** the `skills/generate-changelog` folder into your project.
2. **Run** either command:
   ```bash
   bash skills/generate-changelog/changelog.sh
   # Or directly with Python:
   python3 skills/generate-changelog/generate_changelog.py
   ```
3. **Review** your generated `CHANGELOG.md` at root.

## Sample Output
```markdown
# Changelog

## [v1.2.0] - 2026-11-19

### Added
- **auth:** implement OAuth2 callback verification (`f8a12bc`)
- **ui:** add dark mode toggle button (`a3b8901`)

### Fixed
- **api:** resolve unhandled promise rejection in session cleanup (`d94e11a`)

### Changed
- **core:** optimize SQL index on customer_id (`e45c789`)
```
