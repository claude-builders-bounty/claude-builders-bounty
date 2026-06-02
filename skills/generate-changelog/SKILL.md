# Generate Changelog

Generate a structured `CHANGELOG.md` from git history.

## Use

```bash
bash changelog.sh --repo . --output CHANGELOG.md
```

Claude Code command:

```text
/generate-changelog
```

## What It Does

1. Finds commits since the latest reachable git tag.
2. Skips merge commits.
3. Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
4. Writes a Keep-a-Changelog-style Markdown file.

## Options

```bash
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md
bash changelog.sh --repo /path/to/repo --since v1.2.0 --output CHANGELOG.md
bash changelog.sh --repo /path/to/repo --since 2026-01-01 --until HEAD
```

When no tag exists, the script uses the full branch history.
