# Generate Changelog Skill

Auto-generates a structured CHANGELOG.md from git commit history.

## Usage

```bash
python skills/generate-changelog.py
```

Or via Claude Code:
```
/generate-changelog
```

## How It Works

1. Detects last git tag (if any)
2. Fetches all commits since that tag
3. Auto-categorizes into: Added / Fixed / Changed / Removed
4. Outputs formatted CHANGELOG.md

## Commit Convention

Follows conventional commits for auto-categorization:
- `feat:` / `add:` → Added
- `fix:` / `bug:` → Fixed
- `refactor:` / `update:` → Changed
- `remove:` / `delete:` → Removed

## Output Format

```markdown
# Changelog

## [v1.2.0] - 2026-03-30

### Added
- feat: new user authentication

### Fixed
- fix: login button alignment

### Changed
- refactor: optimize database queries
```

## Requirements

- Python 3.8+
- Git

## License

MIT
