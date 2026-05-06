# CHANGELOG Generator

This tool automatically generates a structured `CHANGELOG.md` from your git history.

## Setup & Usage

1. **Download:** Copy `changelog.sh` to your project root.
2. **Permissions:** Run `chmod +x changelog.sh`.
3. **Execute:** Run `./changelog.sh` to generate/update your `CHANGELOG.md`.

The script fetches all commits since the last git tag and categorizes them into Added, Fixed, Changed, and Removed sections.
