# Git Changelog Generator Skill

An automated git history parser and Keep-a-Changelog formatter. This skill extracts and organizes commits since the last release tag, categorizing them into Added/Fixed/Changed/Removed sections.

## Setup Instructions

1. **Copy the script** to your repository's root directory:
   ```bash
   cp -r skills/generate-changelog/changelog.sh ./
   ```
2. **Make it executable**:
   ```bash
   chmod +x changelog.sh
   ```
3. **Run the generator**:
   ```bash
   ./changelog.sh
   ```
   This will create or prepend to your repository's `CHANGELOG.md`.
