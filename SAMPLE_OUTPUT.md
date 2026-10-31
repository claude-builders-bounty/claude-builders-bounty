# Sample Output — Tagged Repository

Tested against a repository with 9 commits and a `v1.0.0` tag placed 3 commits before HEAD.

```markdown
# Changelog

## [2026-10-31] — Changes since v1.0.0

### Added

- feat: add user profile avatar upload (`7d96c8a`)

### Changed

- perf: optimize image thumbnail generation (`5b20c49`)

### Removed

- remove: drop legacy v1 API endpoints (`29303f5`)
```

# Sample Output — Untagged Repository

Tested against a repository with 3 commits and no tags.

```markdown
# Changelog

## [2026-10-31] — Full History

### Added

- add: new CLI entry point (`be2ae0f`)
- feat: bootstrap project (`a804075`)

### Fixed

- fix: typo in README (`0824d52`)
```
