# Changelog Generator

A zero-dependency Python script that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Features

- ✅ Fetches commits since the last git tag
- ✅ Auto-categorizes into: Added / Fixed / Changed / Removed / Documentation / Testing / Performance / Security
- ✅ Uses conventional commit prefixes
- ✅ Outputs properly formatted Markdown
- ✅ Zero dependencies (stdlib only)

## Setup (3 steps)

```bash
# 1. Copy the script to your project
curl -O https://raw.githubusercontent.com/k2d5rqjpkg-art/claude-review-tool/main/generate-changelog.py

# 2. Make it executable
chmod +x generate-changelog.py

# 3. Run it
python3 generate-changelog.py --repo . --output CHANGELOG.md
```

## Usage

```bash
# Generate CHANGELOG for current repository
python3 generate-changelog.py

# Specify repository path
python3 generate-changelog.py --repo /path/to/repo

# Specify output file
python3 generate-changelog.py --output CHANGELOG.md
```

## Sample Output

```markdown
# Changelog
_Generated: 2026-05-17_

## [v1.0.0] - 2026-05-17

### Added
- User authentication flow

### Fixed
- Memory leak in cache handler
```

## Requirements

- Python 3.6+
- Git repository

## Testing

```bash
# Test on this repository
python3 generate-changelog.py --repo . --output TEST_CHANGELOG.md
```
