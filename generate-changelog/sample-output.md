# Sample Output

Example generated from the real commit history of `sindresorhus/pretty-ms`, using its latest tag `v9.3.0`:

```bash
bash changelog.sh --output /tmp/sample-changelog.md
```

Example output:

```markdown
# Changelog

## [Unreleased] - 2026-05-15

_Changes since `v9.3.0`._

### Added

- Add FAQ explaining why months/years are not supported (9495643)

### Changed

- Meta tweaks (d1d96e1)
```

The no-tag fallback was also checked against `claude-builders-bounty/claude-builders-bounty`, where the script generated from the full project history.
