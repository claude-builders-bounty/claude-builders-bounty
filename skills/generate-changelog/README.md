# Generate Changelog Skill

## Setup (3 steps)
1. Copy `generate_changelog.py` to your project root.
2. Run `python3 generate_changelog.py`.
3. Commit the generated `CHANGELOG.md`.

## Usage
- `/generate-changelog` (if wired as a Claude Code skill) or `python3 generate_changelog.py`.
- Fetches commits since the last git tag; categorizes into Added/Fixed/Changed/Removed.
