# CHANGELOG Generator

> Automatically generate CHANGELOG.md from git history

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

A simple tool that generates a [Keep a Changelog](https://keepachangelog.com/) formatted CHANGELOG.md from your git commit history.

## Features

- ✅ **Automatic Categorization**: Groups commits by type (feat, fix, docs, etc.)
- ✅ **Version Support**: Groups changes by version tags
- ✅ **Unreleased Section**: Shows changes since last tag
- ✅ **Multiple Implementations**: Bash and Python versions
- ✅ **Conventional Commits**: Parses conventional commit messages
- ✅ **Links**: Adds comparison links between versions

## Installation

### Bash Version (Recommended)

```bash
# Clone the repository
git clone https://github.com/ljapptest-art/generate-changelog.git
cd generate-changelog

# Make executable
chmod +x generate-changelog.sh

# Run
./generate-changelog.sh
```

### Python Version

```bash
# Clone the repository
git clone https://github.com/ljapptest-art/generate-changelog.git
cd generate-changelog

# Run
python generate_changelog.py
```

## Usage

### Basic Usage

```bash
# Generate CHANGELOG.md in current directory
./generate-changelog.sh

# Or with Python
python generate_changelog.py
```

### Specify Output File

```bash
# Generate to custom file
./generate-changelog.sh --output MY_CHANGELOG.md

# Or with Python
python generate_changelog.py --output MY_CHANGELOG.md
```

### NPM Integration

Add to your `package.json`:

```json
{
  "scripts": {
    "changelog": "generate-changelog.sh"
  }
}
```

Then run:

```bash
npm run changelog
```

## Output Format

The generated changelog follows [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

## [Unreleased]

### Added
- New feature (['abc1234'](https://github.com/user/repo/commit/abc1234))

## [1.0.0] - 2026-03-27

### Added
- Initial release (['def5678'](https://github.com/user/repo/commit/def5678))

### Fixed
- Bug fix (['ghi9012'](https://github.com/user/repo/commit/ghi9012))
```

## Commit Categories

Commits are automatically categorized based on their prefix:

| Prefix | Category |
|--------|----------|
| `feat`, `feature` | Added |
| `fix` | Fixed |
| `docs` | Documentation |
| `style`, `refactor` | Changed |
| `perf` | Performance |
| `test` | Testing |
| `build` | Build |
| `ci` | CI/CD |
| `chore` | Maintenance |

## How It Works

1. **Get Tags**: Retrieves all version tags sorted by version number
2. **Get Commits**: Gets commits for each version range
3. **Categorize**: Groups commits by their conventional commit prefix
4. **Format**: Generates markdown following Keep a Changelog format
5. **Links**: Adds comparison links between versions

## Requirements

### Bash Version
- Bash 4.0+
- Git

### Python Version
- Python 3.6+
- Git

## Examples

### Sample Output 1: Project with Tags

```markdown
# Changelog

## [Unreleased]

### Added
- New authentication system

## [2.0.0] - 2026-03-27

### Added
- Dashboard redesign
- User preferences

### Fixed
- Login bug

## [1.0.0] - 2026-03-20

### Added
- Initial release
```

### Sample Output 2: Project without Tags

```markdown
# Changelog

## [Unreleased]

### Added
- Feature one
- Feature two

### Fixed
- Bug fix

### Documentation
- Updated README
```

## Comparison Links

The tool automatically generates comparison links:

```markdown
[Unreleased]: https://github.com/user/repo/compare/HEAD..HEAD
[2.0.0]: https://github.com/user/repo/compare/v1.0.0..v2.0.0
[1.0.0]: https://github.com/user/repo/releases/tag/v1.0.0
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Bounty

Created for [Claude Builders Bounty #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1) - $50
