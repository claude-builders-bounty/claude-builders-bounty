# Git Changelog Generator

A simple Python script to automatically generate a structured `CHANGELOG.md` from your git history. It categorizes commits based on their messages and identifies changes since the last tag.

## Features
- Auto-categorization: `Added`, `Fixed`, `Changed`, `Removed`.
- Automatic detection of the latest git tag.
- Clean, markdown-ready output.

## Setup in 2 Steps

1. **Download**: Save `generate_changelog.py` to your project root.
2. **Run**: 
   ```bash
   python generate_changelog.py
   ```

## Example Output
Check the `CHANGELOG.md` file in this repository for a sample of the output generated from our own commits.
