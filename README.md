# Changelog Generator

A simple bash script to generate a structured `CHANGELOG.md` from git history.

## Installation

```bash
# Just copy the script to your project
curl -o changelog.sh https://raw.githubusercontent.com/Hasned-spec/claude-builders-bounty/main/changelog.sh
chmod +x changelog.sh
```

## Usage

```bash
# Generate changelog since last tag (default)
./changelog.sh

# Generate since specific tag
./changelog.sh --since v1.0.0

# Custom output file
./changelog.sh --output CHANGES.md
```

## Features

- Auto-categorizes commits: **Added**, **Fixed**, **Changed**, **Removed**, **Other**
- Follows [Keep a Changelog](https://keepachangelog.com/) format
- Works with conventional commits and infers categories from keywords
- No dependencies beyond git and bash
