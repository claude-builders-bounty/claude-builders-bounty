# Changelog Generator

A simple bash script that automates the creation of a structured `CHANGELOG.md` file by categorizing your recent git commits since the last tag.

## Features
- Fetches commits since the last `git tag` (or since the beginning if no tags exist).
- Automatically categorizes commits using conventional commit detection:
  - `Added` (`feat:`, `add:`)
  - `Fixed` (`fix:`, `bug:`)
  - `Changed` (`refactor:`, `chore:`, `docs:`, etc.)
  - `Removed` (`remove:`, `drop:`)
- Generates markdown files with commit hashes linked to your GitHub repository automatically.

## Installation & Setup (3 Steps)

1. **Download the script to your project root:**
```bash
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/solutions/changelog-generator/generate_changelog.sh
```

2. **Make it executable:**
```bash
chmod +x generate_changelog.sh
```

3. **Run the script:**
```bash
./generate_changelog.sh
```

A `CHANGELOG.md` file will instantly be created or overwritten in your current directory.