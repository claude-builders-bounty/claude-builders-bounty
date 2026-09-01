---
name: generate-changelog
description: Automatically generates or updates CHANGELOG.md from git commit history categorized by Added, Fixed, Changed, and Removed.
---

# Generate Changelog Skill

Run the changelog generation script against the current git repository:

```bash
python3 generate_changelog.py "$@"
```

## Options
- `--version <version>`: Set the release version tag (e.g. `v1.2.0` or `Unreleased`)
- `--since <tag>`: Collect commits starting from a specific git tag or commit SHA
- `--output <file>`: Output file path (default: `CHANGELOG.md`)
- `--stdout`: Print changelog to standard output without writing to file
