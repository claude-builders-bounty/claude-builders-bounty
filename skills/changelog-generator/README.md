# changelog.sh

Generate a structured CHANGELOG.md from git history.

## Usage

```bash
cd your-repo
bash changelog.sh
```

## What it does

1. Detects the last git tag as baseline (or starts from the first commit)
2. Fetches all commits since then
3. Categorizes by conventional commit type into **Added**, **Fixed**, **Changed**, **Removed**
4. Writes a formatted `CHANGELOG.md` with version bump

## Options

| Flag | Description |
|------|-------------|
| `-o FILE` | Write to a custom filename (default: CHANGELOG.md) |
| `-h` | Show help |

## Example output

```
# Changelog

## [0.2.1] — 2026-05-17

### Added
* Add user authentication middleware (abc1234, 2026-05-16)

### Fixed
* Fix login redirect loop (def5678, 2026-05-15)

### Changed
* Refactor database connection pool (ghi9012, 2026-05-14)
```
