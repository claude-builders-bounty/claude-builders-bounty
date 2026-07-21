# CHANGELOG Generator

A Claude Code skill that auto-generates structured `CHANGELOG.md` from git history.

## Setup

```bash
chmod +x changelog.sh
```

## Usage

```bash
# Generate changelog since last tag
bash changelog.sh

# Generate since specific tag
bash changelog.sh v1.0.0
```

Or use in Claude Code: `/generate-changelog`

## How It Works

1. Fetches commits since the last git tag
2. Auto-categorizes into: `Added`, `Fixed`, `Changed`, `Removed`
3. Matches conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.)
4. Outputs a properly formatted `CHANGELOG.md`

## Sample Output

```markdown
# Changelog

## [Unreleased]

### Added
- Add user authentication with OAuth2
- Add dark mode toggle

### Fixed
- Fix memory leak in WebSocket handler
- Fix incorrect date formatting

### Changed
- Refactor database connection pooling
- Improve error messages

### Removed
- Remove deprecated /v1 API endpoints
```
