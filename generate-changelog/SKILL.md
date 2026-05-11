---
name: generate-changelog
description: Generate a structured CHANGELOG.md from the current repository's git history.
---

# Generate Changelog

Use this skill when the user asks to generate release notes or a structured changelog from git commits.

## Command

Run the root command:

```bash
bash changelog.sh
```

Or run the bundled script directly:

```bash
bash generate-changelog/changelog.sh
```

## Workflow

1. Inspect the current repository with `git status --short --branch` so you know which repo is being summarized.
2. Run `bash changelog.sh --dry-run` and review the output.
3. If the output is appropriate, run `bash changelog.sh` to write `CHANGELOG.md`.

## Notes

- The script uses commits since the latest tag. If the repository has no tags, it uses all commits.
- It groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- It does not call external services or require package installation.
