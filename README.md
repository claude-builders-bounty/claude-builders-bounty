# Git Changelog Generator

A simple and robust bash script that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Features
- Fetches commits since the last git tag (or from the initial commit if no tags exist).
- Auto-categorizes commits into `Added`, `Fixed`, `Removed`, and `Changed` based on conventional commit prefixes.
- Outputs a cleanly formatted `CHANGELOG.md` file.

## Setup Instructions

1. **Download the script** into your repository:
   ```bash
   curl -O https://raw.githubusercontent.com/Ishant5436/claude-builders-bounty/main/changelog.sh
   ```
2. **Make it executable**:
   ```bash
   chmod +x changelog.sh
   ```
3. **Run it**:
   ```bash
   ./changelog.sh
   ```

This will instantly generate a `CHANGELOG.md` in your current directory.
