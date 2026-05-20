# CHANGELOG Generator Skill

This Claude Code skill automatically generates a structured `CHANGELOG.md` from a project's git history.

## Installation

1. Copy `SKILL.md` to your project's `.claude/` directory:
   ```bash
   mkdir -p .claude
   cp SKILL.md .claude/
   ```

2. Run the skill:
   ```bash
   claude /generate-changelog
   ```

Or use the standalone bash script:
```bash
chmod +x changelog.sh
./changelog.sh
```

## Usage

```bash
# Generate changelog since last tag
claude /generate-changelog

# Generate changelog for specific version range
claude /generate-changelog v1.0.0..v2.0.0

# Generate changelog for specific number of commits
claude /generate-changelog --last 50
```

## Output Format

The generated `CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

## [Unreleased]

### Added
- New feature for X (#123)

### Fixed
- Bug in Y component (#124)

### Changed
- Updated Z behavior (#125)

### Removed
- Deprecated W functionality (#126)
```

## Features

- Fetches commits since the last git tag
- Auto-categorizes into: Added / Fixed / Changed / Removed / Deprecated / Security
- Includes PR/issue references
- Properly formatted Markdown output
- Configurable version ranges

## Requirements

- Git 2.0+
- Claude Code CLI

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-05-15

### Added
- Implemented user authentication flow (#45)
- Added dark mode support (#47)
- New API endpoint for data export (#51)

### Fixed
- Resolved memory leak in worker thread (#46)
- Fixed timezone handling in scheduler (#49)
- Corrected validation error messages (#52)

### Changed
- Improved database query performance by 40% (#48)
- Updated dependencies to latest versions (#50)

### Removed
- Deprecated legacy API endpoints (#44)

## [1.1.0] - 2026-04-20

### Added
- Initial release features (#1-#43)
```

## License

MIT