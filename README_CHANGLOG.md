# CHANGELOG Generator

This script automatically generates a structured `CHANGELOG.md` from your project's git history.

## Setup

1. Copy `changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run the script: `./changelog.sh`

## How it works

- Fetches commits since the last git tag
- Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- Outputs a properly formatted `CHANGELOG.md`