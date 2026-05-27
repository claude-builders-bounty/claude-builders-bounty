---
name: generate-changelog
description: Auto-generates a structured CHANGELOG.md from git history
version: 1.0.0
author: Claude Builders Bounty
---

# generate-changelog

Generates a structured `CHANGELOG.md` from a project's git history.

## Usage

### As a Bash script:
```bash
chmod +x generate_changelog.sh
./generate_changelog.sh            # Write to CHANGELOG.md
./generate_changelog.sh HISTORY.md # Custom output filename
```

### As a Claude Code Skill:
```
/generate-changelog           # Generate from last tag to HEAD
/generate-changelog v1.0 v2.0 # Custom range
```

## How it works

1. Detects the last git tag (or uses all commits if no tags exist)
2. Parses conventional commit messages
3. Categorizes into: Added, Fixed, Changed, Removed, Deprecated, Security, Performance, Documentation
4. Outputs a properly formatted Markdown file

## Requirements

- bash 4+
- git
- Standard Unix tools (grep, sed, tr)
