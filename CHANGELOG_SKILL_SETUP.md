# Generate Changelog Skill

A bash script + Claude Code skill that generates a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

1. Copy `generate-changelog.sh` (or `generate-changelog.py`) and `SKILL.md` into your git project
2. Make the script executable: `chmod +x generate-changelog.sh` (Linux/macOS)
3. Run it: `bash generate-changelog.sh` or `python generate-changelog.py`

## Features

- Fetches commits since the last git tag
- Auto-categorizes into Added / Fixed / Changed / Removed
- Skips merge commits
- Supports custom tag range and output file
- Works on Linux, macOS, and Windows

## Usage examples

```bash
# Bash version
bash generate-changelog.sh

# Python version (cross-platform)
python generate-changelog.py

# Since a specific tag
python generate-changelog.py --since-tag v1.0.0

# Custom output file
python generate-changelog.py --output RELEASE_NOTES.md
```

## Claude Code integration

If you place `SKILL.md` in your project, Claude Code can run `/generate-changelog` to invoke the script.

## Sample output

See `SAMPLE_OUTPUT.md` for a real example generated from a demo git repository.
