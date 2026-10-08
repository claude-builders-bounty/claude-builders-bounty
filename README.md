# Structured Git Changelog Generator

Automatically parses git commits since the last release tag and compiles a clean, categorized `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) guidelines.

## Quick Setup (3 Steps)

1. **Clone or Copy**: Place `generate_changelog.py` and `changelog.sh` in your project root or scripts directory.
2. **Execute**: Run `bash changelog.sh` (or `python generate_changelog.py`).
3. **Done**: Inspect your updated `CHANGELOG.md` ready for release!

---

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-10-08

### Added
- **auth**: Add OAuth2 Google and GitHub login providers ([a1b2c3d])
- Support export to CSV and Excel format ([e4f5g6h])

### Fixed
- Resolve memory leak in background worker task ([789abc0])
- Correct date parsing for ISO-8601 timestamps ([def1234])

### Changed
- Refactor API client with retry backoff ([567890a])

### Removed
- Deprecate legacy XML endpoints ([bcdef01])
```
