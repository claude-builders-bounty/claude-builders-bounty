# Generate Changelog

A bash script to generate a structured `CHANGELOG.md` from git history using Conventional Commits.

## Setup (3 steps)

1. Copy `generate-changelog` into your project root.
2. Make executable: `chmod +x generate-changelog`.
3. Run: `./generate-changelog > CHANGELOG.md`.

## How it works

- Fetches commits since the last tag; if no tags, uses all commits.
- Categorizes by commit type:
  - **Added**: `feat`, `feature`, `add`
  - **Fixed**: `fix`, `bug`, `patch`
  - **Changed**: `refactor`, `improve`, `update`, `style`, `chore`, `ci`, `build`, `test`
  - **Removed**: `remove`, `delete`, `drop`, `break`
- Outputs markdown sections.

## Example

```bash
$ ./generate-changelog > CHANGELOG.md
```

Sample output:

```markdown
## [Unreleased]

### Added
- feat: add new feature

### Fixed
- fix: resolved bug

### Changed
- refactor: simplify code
- chore: update deps

### Removed
- remove: old module
```

## Notes

- Designed for repositories using Conventional Commits.
- Outputs to stdout; redirect to file as shown.
