# Changelog Generator Skill

## Description
Auto-generates a structured CHANGELOG.md from git history.

## Usage
python changelog.py [repo_path] [output_file]

## Acceptance Criteria
- Fetches commits since last tag
- Auto-categorizes into: Added / Fixed / Changed / Removed
- Outputs properly formatted CHANGELOG.md
- Works on real GitHub repos

## Setup (3 steps)
1. Clone repo
2. Run: python changelog.py . CHANGELOG.md
3. Check output