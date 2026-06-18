# Git Changelog Generator Skill

A lightweight bash script that automatically analyzes a repository's git commit history and generates a structured, categorized `CHANGELOG.md` file.

## Features
- Fetches all commits since the last git tag (or all time if no tags exist).
- Auto-categorizes conventional commits into: `Added`, `Fixed`, `Changed`, and `Removed`.
- Outputs a perfectly formatted markdown document.

## Setup & Usage (3 Steps)

1. Drop the `changelog.sh` script into the root of your git repository.
2. Make the script executable: 
   ```bash
   chmod +x changelog.sh
   ```
3. Run the generator: 
   ```bash
   ./changelog.sh
   ```

A new `CHANGELOG.md` file will be instantly written to your directory containing the neatly categorized git history!
