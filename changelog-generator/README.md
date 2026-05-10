# Auto-Changelog Generator

A simple script to automatically generate a structured `CHANGELOG.md` from your git history. It groups commits into `Added`, `Fixed`, `Changed`, and `Removed` categories based on commit messages.

## Setup Instructions

1. **Download the script**:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/changelog.sh -o changelog.sh
   ```

2. **Make it executable**:
   ```bash
   chmod +x changelog.sh
   ```

3. **Run it in your repository**:
   ```bash
   ./changelog.sh
   ```

This will automatically create or update your `CHANGELOG.md` file with the latest commits since your last git tag!
