# Sample Output

This output was produced with a tagged validation fixture.

Validation command:

```bash
bash changelog.sh --dry-run
```

Output:

```markdown
# Changelog

## Unreleased - 2026-06-25

Generated from commits after `v1.0.0`.

### Added

- Add export format option (`520494b`)

### Fixed

- Handle missing release notes directory (`65128f3`)

### Changed

- Simplify changelog renderer (`46cc838`)

### Removed

- Remove deprecated config alias (`a369bc9`)
```
