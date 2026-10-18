# generate-changelog

A Claude Code skill that generates a structured `CHANGELOG.md` from git history.

## Usage

Invoke with `/generate-changelog` or run `bash changelog.sh`.

## What it does

1. Finds the last git tag (or uses full history if none).
2. Collects commit subjects since that tag.
3. Categorizes each into **Added / Fixed / Changed / Removed / Other**.
4. Writes a formatted `CHANGELOG.md`.

## Setup (3 steps)

1. Copy `changelog.sh` to your project root.
2. Make it executable: `chmod +x changelog.sh`.
3. Run `bash changelog.sh` (optionally pass an output path).

## Sample output

```markdown
# Changelog

## Unreleased (since v1.2.0)

### Added
- feat: add user profile page

### Fixed
- fix: null pointer in checkout flow

### Changed
- refactor: extract payment service

### Removed
- remove: deprecated v1 endpoints
```