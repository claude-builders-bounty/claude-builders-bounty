# Changelog Generator

Auto-generates structured `CHANGELOG.md` from git commit history.

## Setup

```bash
cp changelog.sh /usr/local/bin/
chmod +x /usr/local/bin/changelog.sh
```

## Usage

```bash
# Generate changelog since last tag
bash changelog.sh

# Output to custom file
CHANGELOG_OUTPUT=docs/CHANGELOG.md bash changelog.sh
```

## How It Works

1. Finds the most recent git tag (or first commit if no tags)
2. Reads all commits since that point
3. Categorizes by commit message prefix:
   - `Added`: add, feat, new, introduce, create
   - `Fixed`: fix, bug, patch, resolve, hotfix, correct
   - `Changed`: change, update, modify, refactor, improve, tweak, adjust
   - `Removed`: remove, delete, drop, deprecate, retire
4. Outputs `CHANGELOG.md` with sections

## Sample Output

```markdown
# Changelog

## v1.2.0 (2026-05-05)

### Added
- feat: add dark mode support
- new: user profile page

### Fixed
- fix: login redirect loop
- bug: handle empty search results

### Changed
- refactor: extract auth logic to hook
- improve: reduce bundle size
```
