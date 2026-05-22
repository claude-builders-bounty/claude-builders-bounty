# SKILL: generate-changelog

## Usage

```
/generate-changelog [--version VERSION] [--output FILE]
```

## Description

Automatically generates a structured CHANGELOG.md from the project's git history.

## Features

- Fetches commits since the last git tag
- Auto-categorizes commits: Added, Changed, Fixed, Removed, Security, Docs
- Supports commit links to remote repository
- Configurable output file

## Requirements

- Python 3.8+
- Git repository with commit history

## Examples

```bash
# Generate from last tag
/generate-changelog

# Generate for specific version
/generate-changelog --version v2.0.0

# Output to custom file
/generate-changelog -o HISTORY.md
```
