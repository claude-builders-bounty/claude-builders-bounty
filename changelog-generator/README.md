# Changelog Generator

Generate a structured `CHANGELOG.md` from git history with one command.

## Setup in 3 steps

1. Copy `changelog-generator/changelog.sh` into any git repository.
2. Run `bash changelog-generator/changelog.sh` from the repository root.
3. Commit the generated `CHANGELOG.md`.

## What it does

- Finds commits since the latest reachable git tag.
- Falls back to the full history when the repository has no tags.
- Ignores merge commits to keep the output readable.
- Categorizes entries into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a properly formatted `CHANGELOG.md`.

## Options

```bash
bash changelog-generator/changelog.sh --since v1.2.0
bash changelog-generator/changelog.sh --output docs/CHANGELOG.md
bash changelog-generator/changelog.sh --repo /path/to/project
```

## Categorization rules

- `Added`: `feat:`, add, create, introduce, implement, feature.
- `Fixed`: `fix:`, bug, patch, hotfix, security, vulnerability.
- `Removed`: remove, delete, deprecate, revert.
- `Changed`: everything else.

The rules are intentionally simple and shell-only so the generator works in CI, local terminals, and Claude Code sessions without package installation.

## Sample output

See [`../samples/CHANGELOG.sample.md`](../samples/CHANGELOG.sample.md), generated from this repository with:

```bash
bash changelog-generator/changelog.sh --output samples/CHANGELOG.sample.md
```
