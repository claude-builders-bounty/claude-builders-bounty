# Changelog Generator Skill

Automatically generates structured CHANGELOG.md from git commit history.

## Description

This skill analyzes git commit history since the last tag and generates a structured CHANGELOG.md file with commits categorized into: Added, Fixed, Changed, Removed.

## Features

- **Automatic categorization**: Uses commit message patterns to categorize changes
- **Tag-based versioning**: Starts from the latest git tag, or all commits if no tags exist
- **Multiple output formats**: Markdown formatting with proper headings and lists
- **Flexible invocation**: Can be called via command or integrated into CI/CD pipelines

## Commands

### `/generate-changelog`
Generates a CHANGELOG.md file in the current directory.

**Options:**
- `--output FILE`: Specify output file (default: CHANGELOG.md)
- `--since TAG`: Start from specific tag (default: latest tag)
- `--all`: Include all commits (ignore tags)
- `--format FORMAT`: Output format: markdown, json (default: markdown)

## Usage Examples

```bash
# Generate changelog from latest tag
/generate-changelog

# Generate changelog to specific file
/generate-changelog --output docs/CHANGELOG.md

# Generate changelog from specific tag
/generate-changelog --since v1.0.0

# Generate complete changelog (all commits)
/generate-changelog --all
```

## Installation

1. **Copy the skill files** to your skills directory:
   ```bash
   cp -r changelog-generator/ ~/.openclaw/workspace/skills/
   ```

2. **Restart OpenClaw** or reload skills.

3. **Use the command** in any git repository:
   ```bash
   cd /path/to/your/repo
   /generate-changelog
   ```

## How It Works

1. **Git history analysis**: Uses `git log` to retrieve commit history
2. **Pattern matching**: Categorizes commits based on keywords in commit messages
3. **Version detection**: Identifies tags and organizes changes by version
4. **File generation**: Creates properly formatted CHANGELOG.md

## Categorization Rules

- **Added**: `add`, `create`, `new`, `implement`
- **Fixed**: `fix`, `bug`, `issue`, `error`, `resolve`
- **Changed**: `change`, `update`, `modify`, `refactor`, `improve`
- **Removed**: `remove`, `delete`, `deprecate`, `drop`

## Requirements

- Git installed and available in PATH
- Python 3.6+ (for Python implementation)
- Write permissions in the repository

## License

MIT License - Free to use and modify.