# Changelog Generator

Auto-generates structured CHANGELOG.md from git history.

## Install

```bash
cp changelog.sh /usr/local/bin/changelog
chmod +x /usr/local/bin/changelog
```

## Usage

```bash
# Generate CHANGELOG from commits since last tag
changelog

# Preview without writing
changelog --dry-run
```

## Sample Output

```markdown
# Changelog

## [2026-06-10] — v1.2.0..HEAD

### Added
- User authentication with OAuth2 (abc1234, @dev1)
- Dark mode theme toggle (def5678, @dev2)

### Fixed
- Race condition in payment webhook (ghi9012, @dev1)
- Mobile layout overflow on dashboard (jkl3456, @dev3)

### Changed
- Upgrade to Next.js 15 (mno7890, @dev2)
```

## How It Works

1. Finds the latest git tag
2. Collects commits since that tag
3. Auto-categorizes by conventional commit type (feat=Added, fix=Fixed, etc.)
4. Outputs structured Markdown to CHANGELOG.md