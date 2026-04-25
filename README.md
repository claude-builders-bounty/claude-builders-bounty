# Changelog Generator

Automatically generate a structured CHANGELOG.md from git history.

## Setup

1. Make the script executable:
   ```bash
   chmod +x changelog.sh
   ```

2. Run the script in your git repository:
   ```bash
   ./changelog.sh
   ```

3. Check the generated CHANGELOG.md file

## Usage

The script generates a CHANGELOG.md with changes since the last git tag, categorized into:
- Added (feat)
- Fixed (fix)
- Changed (perf, refactor, style, docs, test, chore)
- Removed (commits containing remove/delete/drop)

Output follows Keep a Changelog format with an [Unreleased] section.