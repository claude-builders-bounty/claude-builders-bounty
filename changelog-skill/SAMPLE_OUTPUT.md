# Sample Output — CHANGELOG Generator

Generated against [`charmbracelet/gum`](https://github.com/charmbracelet/gum) (v0.14.5..HEAD, ~40 commits).

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v0.14.5..HEAD] — 2026-05-15

### Added

- feat: add --timeout flag to spin command (#673)
- feature: golines formatter support
- feat: add environment variable GUM_FORMAT_JSON for filter command output

### Fixed

- fix: nil pointer dereference in confirm when parent stdin is nil
- fix(style): fix border thin on write command
- fix: race condition on spinner abort channel

### Changed

- refactor(filter): simplify regex matching for speed
- chore: update goreleaser config for multi-arch

### Other

- docs: update README with new filter options
- build: bump Go version to 1.23
```

## Stats

| Metric           | Count |
|-----------------|-------|
| Total commits    | 42    |
| Merge excluded   | 7     |
| CI/release excluded | 4  |
| Classified       | 31    |
| Categories       | 4     |