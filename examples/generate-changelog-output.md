# Example output

The generator was tested against this repository after creating a sample git history.

Command:

```bash
python3 scripts/generate_changelog.py --dry-run
```

Output shape:

```markdown
## Unreleased since v0.1.0 - 2026-05-16

### Added

- Add user login flow (abc1234)

### Fixed

- Fix changelog formatting (def5678)

### Changed

- Update README examples (fedcba9)

### Removed

- Remove deprecated setup script (123abcd)
```

Notes:

- The date is generated at runtime.
- Commit hashes come from the target repository.
- When no tag exists, the heading becomes `## Unreleased - YYYY-MM-DD`.
