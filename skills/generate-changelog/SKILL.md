---
name: generate-changelog
description: Generate a structured CHANGELOG.md from commits since the latest git tag.
---

# Generate a changelog

Use the repository's `changelog.sh` script when the user asks for release notes or a changelog. It reads real commit subjects and short hashes; do not invent entries or silently rewrite commit history.

## Usage

```bash
bash changelog.sh --repo /path/to/project --output /path/to/project/CHANGELOG.md
```

The default range is the latest reachable tag through `HEAD`. Use `--since REF` to choose a different starting point, or `--output -` to print Markdown to stdout.

After running it, report the starting ref, output path, and the number of entries in each section. If the project has no tags, say that the full repository history was used.
