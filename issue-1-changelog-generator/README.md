# Changelog Generator

This tool automatically generates a structured `CHANGELOG.md` from your git history. It parses commit messages since the last git tag, categorizes them, and outputs a formatted Markdown file.

## Setup

Follow these 3 simple steps to generate your changelog:

1. **Place the Script:** Place `changelog_generator.py` in the root of your git repository.
2. **Ensure Python 3 is Installed:** Make sure you have Python 3 installed on your system.
3. **Run the Script:** Execute the script from your terminal:
   ```bash
   python changelog_generator.py
   ```

A `CHANGELOG.md` file will be created in your directory with your categorized commits (`Added`, `Fixed`, `Changed`, `Removed`).

## Commit Formatting
To get the best results, use conventional commit prefixes:
- `feat:` or `add:` -> **Added**
- `fix:` or `bug:` -> **Fixed**
- `remove:` or `delete:` -> **Removed**
- Everything else -> **Changed**
