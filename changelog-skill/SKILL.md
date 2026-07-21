# SKILL.md — Changelog Generator

## Description
Generate a structured CHANGELOG.md from git history. Categorizes commits into Breaking Changes, Added, Fixed, Changed, Removed using Conventional Commits format.

## Usage
Trigger this skill by typing `/generate-changelog` or running `python changelog.py`.

## Instructions
1. Run `changelog.py` in project root
2. Script auto-detects last tag and parses commits since then
3. Outputs Keep a Changelog format to stdout or file
4. Supports `--since <tag>`, `--output <file>`, `--unreleased`

## Acceptance Criteria
- Works via `/generate-changelog` command or `bash changelog.sh`
- Fetches commits since last git tag
- Auto-categorizes into: Added / Fixed / Changed / Removed
- Outputs properly formatted CHANGELOG.md
- Tested on real GitHub repo (include sample output in PR)
- README with setup in 3 steps or fewer