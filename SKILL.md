# Skill: Generate Changelog

## Description
Automatically generates a structured CHANGELOG.md from git history, categorizing commits into Added, Fixed, Changed, and Removed sections.

## Usage
Invoke via: `/generate-changelog [tag]`

Or run directly: `bash changelog.sh [tag]`

## Acceptance Criteria
- [x] Works via `/generate-changelog` command or `bash changelog.sh`
- [x] Fetches commits since the last git tag (or last 100 commits if no tag)
- [x] Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- [x] Outputs a properly formatted `CHANGELOG.md`
- [x] README with setup instructions in 3 steps or fewer

## Implementation
- `changelog.sh` - The main bash script
- `SKILL.md` - This skill file for Claude Code invocation
- `README.md` - Setup and usage instructions

## Installation
1. Copy `changelog.sh` to your project root
2. Run `bash changelog.sh` to generate CHANGELOG.md
3. Commit the generated CHANGELOG.md

Or invoke with: `/generate-changelog v1.0.0` to generate from a specific tag.
