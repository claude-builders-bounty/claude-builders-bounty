# Git Changelog Generator

Generates a structured CHANGELOG.md from Git history.

It reads commits since the latest tag and groups them into:

- Added
- Fixed
- Changed
- Removed

## Setup

1. Copy changelog.sh into a Git repository.
2. Make it executable with chmod +x changelog.sh.
3. Run bash changelog.sh.

You can also choose another output file:

bash changelog.sh RELEASE_NOTES.md
