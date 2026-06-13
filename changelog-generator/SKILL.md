---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
trigger: /generate-changelog
---

# Generate Changelog

Generate a `CHANGELOG.md` from the project's git history, categorized by type.

## Usage

Run `bash changelog-generator/changelog.sh` in the project root.

Alternatively, use `--since`, `--output`, or `--repo` flags:

```bash
bash changelog-generator/changelog.sh --since v1.0.0
bash changelog-generator/changelog.sh --output docs/CHANGELOG.md
bash changelog-generator/changelog.sh --repo /path/to/repo
```

## How it works

- Fetches all non-merge commits since the latest git tag
- Auto-categorizes into **Added**, **Fixed**, **Changed**, **Removed**
- Outputs a clean, structured Markdown file
