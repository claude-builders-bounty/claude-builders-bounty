# CHANGELOG Generator Skill

This skill allows Claude Code to generate a structured `CHANGELOG.md` file directly from the repository's git history.

## Features
- **Auto-categorization:** Groups commits into Added, Fixed, Changed, Removed, and Docs.
- **Git Native:** Uses `git log` and `git describe` to find commits since the last tag.
- **Zero Dependencies:** Pure Python 3 script.
- **Markdown Output:** Generates a professional, easy-to-read `CHANGELOG.md`.

## Setup
1. Copy `generate_changelog.py` to your repository.
2. Make it executable: `chmod +x generate_changelog.py`

## Usage
Run the script to generate or update your `CHANGELOG.md`:
```bash
python3 generate_changelog.py
```

## Claude Code Integration
Add the following to your `CLAUDE.md` to enable the `/generate-changelog` command:

```markdown
- **Generate Changelog:** `/generate-changelog` -> Run `python3 generate_changelog.py`
```
