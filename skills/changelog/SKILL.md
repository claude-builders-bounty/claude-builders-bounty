---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, auto-categorizing commits into Added/Fixed/Changed/Removed sections.
---

# /generate-changelog

Generate a structured `CHANGELOG.md` from this project's git history.

## Steps

1. Run the changelog generator:
   ```bash
   bash skills/changelog/changelog.sh
   ```

2. If you want changes since a specific tag:
   ```bash
   bash skills/changelog/changelog.sh --since v1.0.0
   ```

3. Review the generated `CHANGELOG.md` and present it to the user.

## What it does

- Fetches all commits since the last git tag (or full history if no tags)
- Parses conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.)
- Also recognizes natural language prefixes (`Add`, `Fix`, `Remove`, `Update`, etc.)
- Categorizes into: **Added** / **Fixed** / **Changed** / **Removed** / **Other**
- Outputs a properly formatted Markdown changelog

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--since <tag>` | Latest tag | Start point for commit range |
| `--output <file>` | `CHANGELOG.md` | Output file path |
