# Changelog Generator

A simple, dependency-free bash script that generates a structured `CHANGELOG.md` from your git history.

## Setup Instructions

1. Make the script executable:
   `chmod +x changelog.sh`

2. Run the script:
   `./changelog.sh > CHANGELOG.md`

3. Done! The script automatically fetches commits since your last git tag (or all commits if no tags exist) and categorizes them into Added, Fixed, Changed, and Removed based on commit messages.
