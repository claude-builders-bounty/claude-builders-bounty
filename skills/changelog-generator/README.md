# Changelog Generator

Generate a structured `CHANGELOG.md` from git history.

## Setup

```bash
chmod +x changelog.sh
```

## Usage

```bash
# Generate CHANGELOG.md from the last tag to HEAD
./changelog.sh

# Specify output file
./changelog.sh --output RELEASE_NOTES.md
```

## How It Works

1. Detects the most recent git tag
2. Collects all commits since that tag
3. Auto-categorizes into **Added**, **Fixed**, **Changed**, and **Removed** using conventional commit prefixes (`feat:`, `fix:`, `refactor:`, `remove:`, etc.)
4. Outputs a clean Markdown changelog following [keepachangelog.com](https://keepachangelog.com) conventions

## Example Output

```markdown
# Changelog

## v0.1.0 (2026-05-11)

### Added
- feat: add --bounty-only flag
- implement user authentication

### Fixed
- fix: handle empty response
- bug: resolve race condition

### Changed
- refactor: simplify config parsing
- docs: update README
```
