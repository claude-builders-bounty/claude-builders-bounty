---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when a project needs a Markdown changelog generated from recent
git commits.

## What it does

The bundled `changelog.sh` script:

- finds the most recent git tag automatically;
- collects commits from that tag to `HEAD`;
- groups commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`;
- writes a formatted `CHANGELOG.md`.

## Usage

From the root of any git repository:

```bash
bash generate-changelog/changelog.sh
```

Optional flags:

```bash
bash generate-changelog/changelog.sh --output docs/CHANGELOG.md
bash generate-changelog/changelog.sh --from v1.2.0 --to HEAD
bash generate-changelog/changelog.sh --dry-run
```

## Categorization rules

- `feat`, `feature`, `add` -> `Added`
- `fix`, `bugfix`, `hotfix`, `patch` -> `Fixed`
- `remove`, `delete`, `drop`, `deprecate` -> `Removed`
- everything else -> `Changed`

