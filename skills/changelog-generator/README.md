# Changelog Generator Skill

Automatically generate a structured `CHANGELOG.md` based on your project's git history. 
Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed` using standard conventional commits prefixes.

## Setup

1. Copy the `skills/changelog-generator` directory into your `.gemini/config/skills/` (or `.claude/skills/` if using Claude Code).
2. Make the script executable: `chmod +x skills/changelog-generator/changelog.sh`
3. Trigger the skill by typing `/generate-changelog` in your AI CLI tool!

## Example Output

```markdown
## [2026-05-24]

### Added
- Feature A
- New API endpoint

### Fixed
- Bug in the login screen

### Changed
- Refactored authentication module
```
