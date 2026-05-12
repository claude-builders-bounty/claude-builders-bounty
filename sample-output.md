# Sample Output

The script was tested on a temporary git repository with tag `v0.1.0` and five commits after the tag.

Command:

```bash
bash changelog.sh
```

Generated output:

```markdown
# Changelog

All notable changes are generated from git commits since v0.1.0.

## Unreleased - 2026-05-12

### Added

- feat: add export command (56bc1c9)
- add README usage example (4e4bc3a)

### Fixed

- fix: handle empty input files (3c3ef6d)

### Changed

- docs: update setup notes (7b3f732)

### Removed

- remove deprecated config option (0f52f77)
```

