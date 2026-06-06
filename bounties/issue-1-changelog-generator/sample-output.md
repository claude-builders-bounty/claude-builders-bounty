# Sample Output

## Real Repo Demo

Tested on the `claude-builders-bounty` repository, which had no tags at the time of the demo:

```md
# Changelog

Generated on 2026-06-06 from Git history from all commits.

## Unreleased

### Added

- feat: initial README with bounty board (1aeae2a)

### Fixed

- No changes.

### Changed

- No changes.

### Removed

- No changes.
```

## Tagged Repo Demo

Tested on a local Git repository with a `v1.0.0` tag and three commits after the tag:

```md
# Changelog

Generated on 2026-06-06 from Git history since `v1.0.0`.

## Unreleased

### Added

- feat: add webhook endpoint (8b67a0a)

### Fixed

- fix: handle empty payloads (1f354b0)

### Changed

- chore: update release notes (74d2c91)

### Removed

- remove deprecated config flag (2a04dd5)
```
