---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Auto-categorizes commits into Added / Fixed / Changed / Removed using conventional commit prefixes and keyword scanning. Handles no-tag repos, supports --since and --dry-run.
---

Generate a structured CHANGELOG.md from this repository's git history.

## What you'll do

1. Run `bash scripts/changelog.sh` (or with flags below) from the repository root.
2. The script will auto-detect the last git tag (or fall back to the first commit if there are no tags).
3. Commits are categorized as **Added / Fixed / Changed / Removed** using conventional-commit prefixes and keyword scanning.
4. The result is written to `CHANGELOG.md` in the repo root.

## Flags

| Flag | Description |
|------|-------------|
| `--since <tag\|date>` | Override the range (e.g. `v1.2.0` or `2024-01-01`) |
| `--output <file>` | Write to a custom file (default: `CHANGELOG.md`) |
| `--dry-run` | Preview output in terminal without writing any files |
| `--no-color` | Disable ANSI color output |
| `--version <label>` | Override the version heading (default: auto-detected next patch) |

## Examples

```bash
# Standard — auto-detect range, write CHANGELOG.md
bash scripts/changelog.sh

# Preview without writing (great for CI checks)
bash scripts/changelog.sh --dry-run

# Commits since a specific tag
bash scripts/changelog.sh --since v1.0.0

# Commits since a date
bash scripts/changelog.sh --since 2024-06-01

# Write to a different file with a version label
bash scripts/changelog.sh --version v2.0.0 --output RELEASE_NOTES.md
```

## Categorization rules

Commits are matched in priority order:

1. **Conventional commit prefix** (`feat:`, `fix:`, `remove:`, `refactor:`, etc.)
2. **Keyword scan** in the subject line (`added`, `fixed`, `resolved`, `removed`, …)
3. **Other** bucket for anything that doesn't match

Merge commits are excluded automatically (`--no-merges`).

## Invoke this skill

When the user types `/generate-changelog` (with optional flags), run:

```bash
bash scripts/changelog.sh $ARGS
```

Then show them the summary table and confirm the output file path.
If `--dry-run` is used, display the preview inline and do not write any files.
