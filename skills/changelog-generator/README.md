# Changelog Generator

Auto-generate a structured CHANGELOG.md from your git history.

## Installation (2 steps)

```bash
git clone https://github.com/JuanM94/claude-builders-bounty.git
cp claude-builders-bounty/skills/changelog-generator/changelog.sh /usr/local/bin/generate-changelog
```

## Usage

```bash
# Generate CHANGELOG.md in current directory
bash changelog.sh

# Specify output file
bash changelog.sh MY_CHANGELOG.md
```

## How It Works

1. Finds the latest git tag (or uses first commit if no tags exist)
2. Collects all commits since that reference point
3. Auto-categorizes by commit message keywords:
   - **Added**: `feat`, `add`, `new`, `create`, `implement`
   - **Fixed**: `fix`, `bug`, `patch`, `resolve`
   - **Changed**: `update`, `refactor`, `improve`, `enhance`
   - **Removed**: `remove`, `delete`, `drop`, `deprecate`
4. Handles conventional commit prefixes (`feat:`, `fix:`, etc.)
5. Outputs a clean, formatted CHANGELOG.md

## Sample Output

```markdown
# Changelog

## [Unreleased] — 2026-03-31

> Changes since v1.2.0

### Added
- User authentication module (`a1b2c3d`)
- Dark mode support (`e4f5g6h`)

### Fixed
- Login redirect loop (`i7j8k9l`)

### Changed
- Updated dependencies (`m0n1o2p`)
- Refactored database layer (`q3r4s5t`)

### Removed
- Deprecated v1 API endpoints (`u6v7w8x`)
```

## Requirements

- Bash 4.0+
- Git
