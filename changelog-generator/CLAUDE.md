# Changelog Generator

## Commands
- `chmod +x claude-changelog.sh` - Make executable
- `./claude-changelog.sh [from-tag] [to-tag]` - Generate changelog

## Implementation Notes
- Uses git log with format "%h %s" for compact output
- Supports tag range comparisons
- Categorizes by conventional commit prefixes
