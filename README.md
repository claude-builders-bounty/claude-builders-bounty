# changelog.sh

A bash script that generates a structured CHANGELOG.md from git history.

## Setup

1. Place `changelog.sh` in your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run: `bash changelog.sh`

## How it works

Scans commits since the last git tag and categorizes them by conventional commit type.
