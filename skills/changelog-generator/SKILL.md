# Changelog Generator

## Description
Generates a structured `CHANGELOG.md` from a project's git history, auto-categorizing commits into `Added`, `Fixed`, `Changed`, and `Removed` sections.

## Usage
- **Command:** `/generate-changelog`
- **Alternative:** `bash changelog.sh`

## How it works
1. Fetches commits since the last git tag (or all commits if no tags exist)
2. Parses commit messages using conventional commit prefixes:
   - `feat:` → Added
   - `fix:` → Fixed
   - `refactor:`, `perf:`, `style:` → Changed
   - `chore:`, `docs:`, `test:` → Changed (if no other match)
   - `revert:`, `remove:` → Removed
3. Groups commits by category and outputs a formatted `CHANGELOG.md`

## Requirements
- Git repository with commit history
- Bash shell

## Example output