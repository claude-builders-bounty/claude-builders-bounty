# Auto-Changelog Generator

A zero-dependency Python script that automatically generates a structured `CHANGELOG.md` file from your project's git history.

## Features
- Fetches all commits since the last git tag (or all commits if no tags exist).
- Parses Conventional Commits (feat, fix, refactor, remove) and categorizes them automatically.
- Outputs into a perfectly formatted Markdown file with sections: `Added`, `Fixed`, `Changed`, `Removed`.

## Setup & Usage (3 Steps)

1. **Download the script**:
   ```bash
   curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/skills/generate-changelog/changelog.py
   chmod +x changelog.py
   ```
2. **Run it inside your git repository**:
   ```bash
   python changelog.py
   ```
3. **Review**:
   A `CHANGELOG.md` file has been generated in your current directory! Open it to see your categorized commits.
