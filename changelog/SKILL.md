---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, grouped into Added, Fixed, Changed, and Removed sections.
---

# Generate Changelog

Use this skill when a project needs a readable `CHANGELOG.md` created from its git history.

## What It Does

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Reads commits from that tag to `HEAD`; if no tag exists, it reads all commits.
- Groups commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a formatted `CHANGELOG.md` or prints it for review.

## Usage

Generate `CHANGELOG.md`:

```bash
bash changelog.sh
```

Preview without writing:

```bash
bash changelog.sh --stdout
```

Write to a custom path:

```bash
bash changelog.sh --output docs/CHANGELOG.md
```

## Verification

Run the generator on a real git repository:

```bash
python scripts/generate_changelog.py --stdout
```
