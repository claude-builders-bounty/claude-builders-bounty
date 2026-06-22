---
name: generate-changelog
description: Generate a structured CHANGELOG.md from the current repository's git history.
---

# Generate Changelog

Use this skill when the user asks for `/generate-changelog`, release notes, or a structured CHANGELOG generated from git history.

## Command

Run this from the repository root:

```bash
bash changelog.sh
```

The command finds the latest git tag, reads commits from that tag through `HEAD`, categorizes them into `Added`, `Fixed`, `Changed`, and `Removed`, then writes `CHANGELOG.md`.

## Options

```bash
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md
bash changelog.sh --since-tag v1.2.0
bash changelog.sh --stdout
```

## Review Checklist

- Confirm the latest tag is the intended release boundary.
- Read the generated sections and move any ambiguous entry to the best category.
- Commit both the source change and the generated `CHANGELOG.md` when it is part of the requested deliverable.
