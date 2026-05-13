# generate-changelog

Automatically generate a structured CHANGELOG.md from a project's git history.

## Usage

Run /generate-changelog or python3 scripts/generate_changelog.py

## What it does

1. Detects the last git tag
2. Fetches all commits since that tag
3. Categorizes commits into: **Added**, **Fixed**, **Changed**, **Removed**
4. Outputs a properly formatted CHANGELOG.md

## Categories

- eat: / dd: → Added
- ix: → Fixed
- chore: / 
efactor: / change: → Changed
- 
emove: / delete: → Removed

## Output Format

Follows [Keep a Changelog](https://keepachangelog.com/) specification.
