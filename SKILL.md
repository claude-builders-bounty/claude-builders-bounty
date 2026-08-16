---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a Git repository's commits since its latest tag. Use when a user asks to produce, update, or draft release notes or a changelog from Git history, including requests phrased as /generate-changelog.
---

# Generate Changelog

Create a release-ready Markdown changelog from commits made after the latest Git tag.

## Workflow

1. Run `python scripts/generate_changelog.py` from the target repository root.
2. Review uncategorized commit subjects; use `--include-merges` only when merge commits are meaningful release notes.
3. Edit the generated wording only when repository-specific language is needed, then commit `CHANGELOG.md`.

## Behavior

- Detect the latest reachable tag automatically. If no tag exists, include the complete repository history.
- Write `CHANGELOG.md` by default, or pass `--output path/to/file.md`.
- Categorize conventional commits and plain-language subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Include commit short hashes for traceability and omit merge commits by default.

## Examples

```bash
python scripts/generate_changelog.py
python scripts/generate_changelog.py --output docs/CHANGELOG.md
python scripts/generate_changelog.py --since v1.4.0 --include-merges
```

## Resource

Use `scripts/generate_changelog.py` for deterministic generation. It requires Git and Python 3.9 or later.
