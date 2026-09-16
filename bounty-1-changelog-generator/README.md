# Auto Changelog Generator

A simple bash script to automatically generate a structured `CHANGELOG.md` from a project's git history.

## Setup Instructions

1. Copy `changelog.sh` into your project's repository.
2. Make it executable: `chmod +x changelog.sh`
3. Run the script: `./changelog.sh`

The script will fetch commits since the last tag (or all commits if no tags exist), categorize them (Added, Fixed, Changed, Removed), and output a `CHANGELOG.md` file.
