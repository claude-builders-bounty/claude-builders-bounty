# Changelog Generator Skill

A simple, dependency-free bash script to automatically generate a structured `CHANGELOG.md` from your project's git history.

## Setup Instructions

1. **Download the script**:
   Copy `changelog.sh` into your project's root directory.
2. **Make it executable**:
   Run `chmod +x changelog.sh` in your terminal.
3. **Generate your changelog**:
   Run `./changelog.sh` to extract commits since the last tag and categorize them into `CHANGELOG.md`.

## Features
- Intelligently parses git commits since the last semantic tag.
- Auto-categorizes conventional commits into **Added**, **Fixed**, **Changed**, and **Removed** sections.
- Ready to use directly via bash or Claude Code shell execution.
