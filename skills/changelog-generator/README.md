# CHANGELOG Generator Skill

A Claude Code skill + standalone bash script that auto-generates structured CHANGELOG.md from git history.

## Quick Start

```bash
# 1. Make executable
chmod +x skills/changelog-generator/changelog.sh

# 2. Run
bash skills/changelog-generator/changelog.sh

# 3. (Optional) Install globally
sudo cp skills/changelog-generator/changelog.sh /usr/local/bin/changelog
```

## Features

- **Auto-categorization**: Commits are sorted into Added, Fixed, Changed, Removed
- **Conventional Commits**: Full support for `feat:`, `fix:`, `chore:`, `docs:`, etc.
- **Keyword Fallback**: For non-conventional commits, intelligently guesses category
- **Tag-aware**: Automatically detects the last git tag and generates changes since then
- **Configurable**: Limit commit count, set custom output file, specify starting tag
- **Zero Dependencies**: Pure bash, runs on any system with git installed
- **Merge Filtering**: Automatically excludes merge commits from the changelog

## Usage

```bash
# Generate changelog for current repo
changelog.sh

# From a specific tag
changelog.sh --since v1.0.0

# Custom output file
changelog.sh --output RELEASE_NOTES.md

# Limit commits
changelog.sh --limit 200

# Combine options
changelog.sh --since v2.0.0 --output docs/CHANGELOG.md --limit 500
```

## Sample Output

```markdown
# Changelog

## [Unreleased]

### Added
- User authentication with OAuth2 (a1b2c3d)
- Dark mode toggle in settings (e4f5g6h)

### Fixed
- Memory leak in WebSocket handler (i7j8k9l)
- Race condition in task scheduler (m0n1o2p)

### Changed
- Updated React to v19 (q3r4s5t)
- Improved error messages for API failures (u6v7w8x)

---

_Generated on 2026-05-21 from 100 commits._
```

## Claude Code Integration

The `SKILL.md` file contains the Claude Code skill definition. When the user asks to generate a changelog, Claude Code runs the bundled script automatically.

## Testing

```bash
# Test on this repo
cd /tmp && git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git test-repo
cd test-repo
bash /path/to/changelog.sh --limit 20
cat CHANGELOG.md
```
