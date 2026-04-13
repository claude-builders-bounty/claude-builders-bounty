# SKILL.md - CHANGELOG Generator

Generate CHANGELOG.md from git history.

## Usage

`
/generate-changelog
bash changelog.sh
`

## What it does

1. Finds the last git tag
2. Collects all commits since that point
3. Categorizes by prefix (feat->Added, fix->Fixed, etc.)
4. Outputs CHANGELOG.md

## Requirements

- git, grep, sed
- No external dependencies
