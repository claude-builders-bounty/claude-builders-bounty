# Git History CHANGELOG Generator

Generate structured CHANGELOG.md from git history.

## Installation

```bash
chmod +x generate-changelog.sh
./generate-changelog.sh
```

## Usage

```bash
# Generate from current branch
./generate-changelog.sh

# Generate from specific branch
./generate-changelog.sh feature-branch
```

## Features

- Automatic category detection (features, fixes, other)
- Configurable commit limits
- Standard CHANGELOG.md format
- Git history integration
