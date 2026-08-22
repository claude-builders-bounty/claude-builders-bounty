# Git Changelog Generator

A simple bash script to automatically generate a structured `CHANGELOG.md` from your git history. It categorizes commits since your last git tag into: `Added`, `Fixed`, `Changed`, and `Removed`.

## Setup Instructions

1. Download the script to your project:
   ```bash
   curl -o changelog.sh https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog.sh
   ```
2. Make it executable:
   ```bash
   chmod +x changelog.sh
   ```
3. Run it!
   ```bash
   ./changelog.sh
   ```

A fresh `CHANGELOG.md` file will be generated in your current directory!
