# Changelog Generator Skill

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from your project's git history.

## Features

- **Auto-categorization**: Commits are automatically sorted into `Added`, `Fixed`, `Changed`, and `Removed` sections
- **Conventional commit support**: Recognizes standard prefixes like `feat:`, `fix:`, `refactor:`, etc.
- **Tag-based**: Fetches commits since the last git tag for incremental updates
- **Flexible output**: Customizable output file and starting tag
- **No dependencies**: Pure bash script, works on any system with git

## Installation

1. Copy the `changelog.sh` script to your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `bash changelog.sh`

## Usage

### Basic usage