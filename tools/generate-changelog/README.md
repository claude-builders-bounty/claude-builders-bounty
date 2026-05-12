# Generate Changelog

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy `changelog.sh` into a git repository.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Usage

```bash
bash changelog.sh
```

The script finds the latest reachable git tag and reads commits from that tag to `HEAD`. If the repository has no tags, it reads all commits. It writes a Keep a Changelog-style file with `Added`, `Fixed`, `Changed`, and `Removed` sections.

## Categorization Rules

- `feat`, `add`, `new`, `create` -> `Added`
- `fix`, `bug`, `patch`, `repair` -> `Fixed`
- `remove`, `delete`, `drop`, `deprecate` -> `Removed`
- everything else -> `Changed`

## Sample Output

Tested against this repository after the latest tag lookup fell back to all commits:

```markdown
# Changelog

## Unreleased

_Generated from git commits since repository start._

### Added

- Add Next.js SQLite SaaS CLAUDE template

### Fixed

- No matching commits.

### Changed

- Initial commit

### Removed

- No matching commits.
```
