---
name: generate-changelog
description: "Generate structured CHANGELOG.md from git history using conventional commits."
tags: [git, changelog, release, conventional-commits]
---

# Generate Changelog

Generates Keep a Changelog format from conventional commits.

## Usage

```bash
bash changelog.sh --version 1.0.0 --output CHANGELOG.md
```

## Features

- Parses conventional commits (feat, fix, chore, etc.)
- Breaking change detection
- GitHub commit links
- Incremental updates (--append)
- Python + Bash wrapper
