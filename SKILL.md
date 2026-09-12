# CHANGELOG Skill

## Commands
- `/generate-changelog`: generate structured changelog for commits since last tag
- `bash changelog.sh`: same behavior (fallback)

## Behavior
1. Detect latest annotated tag.
2. Collect commits after that tag (`tag..HEAD`), or all history if no tag exists.
3. Categorize commit messages into:
   - Added
   - Fixed
   - Changed
   - Removed
4. Emit `CHANGELOG.md` in markdown format.

## Usage (3 steps)
1. Ensure repository has Git history and tags.
2. Run `bash changelog.sh`.
3. Commit and share `CHANGELOG.md`.
