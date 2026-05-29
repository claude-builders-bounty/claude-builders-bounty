# Changelog Generator Skill

This skill provides a bash script (`changelog.sh`) that automatically generates a structured CHANGELOG.md from git history.

## Features

- Generates changelog from commits since the last git tag
- Automatically categorizes commits into: Added, Fixed, Changed, Deprecated, Removed, Security
- Supports both manual execution (`bash changelog.sh`) and command usage (`/generate-changelog`)
- Can write directly to CHANGELOG.md with `--write` flag

## Usage

### Manual Execution

```bash
# Generate changelog output to stdout
bash changelog.sh

# Write changelog directly to CHANGELOG.md
bash changelog.sh --write
```

### As a Command

After installing this skill, you can use:
```
/generate-changelog
```

This will generate the changelog and display it in the chat.

## How It Works

1. The script finds the most recent git tag
2. Gets all commits since that tag (or all commits if no tags exist)
3. Categorizes each commit based on keywords in the subject:
   - Added: feat, feature, added
   - Fixed: fix, fixed, bugfix
   - Changed: change, changed, refactor, perf, performance
   - Deprecated: deprecated, deprecation
   - Removed: removed, remove, delete
   - Security: security, sec
4. Generates a markdown changelog with sections for each category
5. Includes today's date in the Unreleased section

## Installation

Copy `changelog.sh` to your project directory and make it executable:
```bash
cp path/to/changelog.sh .
chmod +x changelog.sh
```

## Example Output

```markdown
# Changelog

## [Unreleased] - 2026-05-30

### Added
- Add user authentication system
- Implement data validation

### Fixed
- Fix login redirect issue
- Resolve memory leak in data processing

### Changed
- Refactor API service layer
- Update dependencies to latest versions
```