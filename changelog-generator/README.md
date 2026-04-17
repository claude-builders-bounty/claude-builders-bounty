# Claude Changelog Generator

Generate structured CHANGELOG from git history.

## Usage

```bash
# Generate changelog for recent commits
./claude-changelog.sh

# Generate changelog between two tags
./claude-changelog.sh v1.0.0 v2.0.0

# Generate and save to file
./claude-changelog.sh > CHANGELOG.md
```

## Features

- Categorizes commits into: Features, Bug Fixes, Other
- Supports tag-based ranges
- Color output (when supported)
- Works with any git repo

## Requirements

- git
- bash 4.0+
