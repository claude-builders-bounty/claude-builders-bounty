---
name: changelog-generator
version: 1.0.0
description: "Generate structured CHANGELOG.md from git history with auto-categorization of commits into Added/Fixed/Changed/Removed"
author: BetsyMalthus
---

# CHANGELOG Generator Skill

A Claude Code skill that automatically generates a structured CHANGELOG.md from a project's git history.

## Features

- **Auto-categorization**: Classifies commits into Added/Fixed/Changed/Removed based on commit message patterns
- **Tag-based generation**: Fetches commits since the last git tag
- **Multiple formats**: Supports Markdown, JSON, and plain text output
- **Git integration**: Works with any git repository
- **Easy to use**: Simple command-line interface and Claude Code integration

## Installation

### As a Claude Code Skill

1. Copy this folder to your workspace
2. Add to your Claude Code configuration
3. Use `/generate-changelog` command

### Standalone Usage

```bash
# Make the script executable
chmod +x scripts/generate_changelog.py

# Generate CHANGELOG for current directory
./scripts/generate_changelog.py

# Generate CHANGELOG for specific repo
./scripts/generate_changelog.py /path/to/repo

# Generate with custom output file
./scripts/generate_changelog.py --output CUSTOM_CHANGELOG.md
```

## Usage Examples

### Claude Code Integration

```
/generate-changelog
/generate-changelog --repo /path/to/repository
/generate-changelog --since v1.0.0
/generate-changelog --output PROJECT_CHANGELOG.md
```

### Command Line

```bash
# Basic usage (current directory)
python scripts/generate_changelog.py

# Specific repository
python scripts/generate_changelog.py ~/projects/my-app

# Custom date range
python scripts/generate_changelog.py --since "2024-01-01"

# Custom tag
python scripts/generate_changelog.py --since-tag v1.2.0

# Output to file
python scripts/generate_changelog.py --output RELEASE_NOTES.md
```

## Output Format

The generated CHANGELOG.md follows the Keep a Changelog format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Feature description

### Changed
- Change description

### Fixed
- Bug fix description

### Removed
- Removal description

## [1.0.0] - 2024-01-01

### Added
- Initial release
```

## Configuration

Create a `.changelogrc` file in your project root:

```json
{
  "categories": {
    "added": ["feat", "add", "new"],
    "fixed": ["fix", "bug", "patch"],
    "changed": ["change", "update", "modify"],
    "removed": ["remove", "delete", "deprecate"]
  },
  "ignore_patterns": ["^Merge", "^Revert"],
  "template": "keepachangelog"
}
```

## Tools

This skill provides the following tools:

### generate_changelog
Generates a structured CHANGELOG from git history.

**Parameters:**
- `repo_path` (optional): Path to git repository (default: current directory)
- `since_tag` (optional): Generate from specific tag (default: last tag)
- `output_file` (optional): Output file path (default: CHANGELOG.md)
- `format` (optional): Output format: markdown, json, text (default: markdown)

**Example:**
```python
from scripts.generate_changelog import generate_changelog

changelog = generate_changelog(
    repo_path=".",
    since_tag="v1.0.0",
    output_file="CHANGELOG.md"
)
```

## Implementation Details

The skill uses:
- `git log` command to fetch commit history
- Regular expressions for commit categorization
- Semantic versioning detection for tag parsing
- Configurable templates for output formatting

## Testing

Test on a real repository:

```bash
# Clone a test repo
git clone https://github.com/example/test-repo.git

# Generate changelog
cd test-repo
python ../scripts/generate_changelog.py

# View generated CHANGELOG.md
cat CHANGELOG.md
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request