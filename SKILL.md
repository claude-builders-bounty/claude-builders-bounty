# Generate Changelog

Use this skill when a repository needs a structured `CHANGELOG.md` generated from git history.

## Command

Run:

```bash
bash changelog.sh
```

Optional custom output path:

```bash
bash changelog.sh docs/CHANGELOG.md
```

## What It Does

- Finds the latest reachable git tag.
- Collects non-merge commits since that tag, or the full history if no tag exists.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown `CHANGELOG.md` with commit links when the origin remote is on GitHub.

