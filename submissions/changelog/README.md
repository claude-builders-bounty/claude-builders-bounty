# CHANGELOG Generator

Generate structured CHANGELOG.md from git history with one command.

## Usage
```bash
bash changelog.sh [since_tag] [output_file]
```

## Features
- Auto-categorizes commits: Added / Fixed / Changed / Removed
- Works since last git tag (or full history if no tags)
- Outputs properly formatted CHANGELOG.md

## Example
```bash
cd your-project
bash changelog.sh v1.0 CHANGELOG.md
```

## Sample Output
From testing on a real repo (lead-hunter):
```markdown
# Changelog

## feat: Add another feature

### Added
- feat: Add another feature

### Changed
- Normal update without prefix
```
