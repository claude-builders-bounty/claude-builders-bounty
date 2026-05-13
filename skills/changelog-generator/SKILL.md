---
name: changelog-generator
description: Generate a structured CHANGELOG.md from a Git repository's commit history.
---

# Changelog Generator

Use this skill when a project needs a quick, structured changelog from git history.

## Command

Run the bundled script from the target repository:

```bash
bash changelog.sh
```

Common options:

```bash
bash changelog.sh --output RELEASE_NOTES.md
bash changelog.sh --repo /path/to/repo
bash changelog.sh --reverse
```

## Output

The script writes Markdown with `Added`, `Fixed`, `Changed`, `Removed`, and `Other` sections. It uses commits since the latest git tag when one exists, and all history when the repository has no tags.

## Validation

Before relying on local changes to the script, run:

```bash
bash test_changelog.sh
```
