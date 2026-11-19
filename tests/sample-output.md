# Sample output of the generator

Executed `node changelog.js .` inside a test repository with commits since `v1.0.0`:

```
feat: add batch export
fix: login rate limiter
```

Resulting `CHANGELOG.md`:

```
# Changelog

Generated from git log v1.0.0..HEAD on <timestamp>

## [Unreleased]

### Added
- feat: add batch export

### Changed
- (none)

### Fixed
- fix: login rate limiter

### Removed
- (none)
```

Verified against `git log v1.0.0..HEAD --pretty=format:'%s'` — the only commits since the tag are the two above, which land in `Added` and `Fixed` respectively.
