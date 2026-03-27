# Sample CHANGELOG.md Output

This file demonstrates the output of `generate-changelog.sh`.

Run on a sample repository with the following git history:

```bash
$ git log --oneline
abc1234 feat: Add user authentication
def5678 fix: Memory leak in cache
ghi9012 refactor: Improve API performance
jkl3456 remove: Deprecated legacy endpoints
mno7890 feat(api): Add rate limiting
```

## Generated Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Rate limiting
- User authentication

### Fixed
- Memory leak in cache

### Changed
- Improve API performance

### Removed
- Deprecated legacy endpoints

## [1.0.0] - 2026-01-15

### Added
- Initial release with core features
```

## Notes

1. Commit messages are cleaned of prefixes automatically
2. First letter is capitalized
3. Categories are sorted alphabetically
4. Duplicate entries are removed
5. Each version includes the release date from the git tag