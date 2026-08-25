# generate-changelog

Generate a Keep-a-Changelog formatted `CHANGELOG.md` from git history.

## Trigger

`/generate-changelog`

## Instructions

1. Run `python3 changelog.py --dry-run` in the target repository to preview output.
2. If the categories look correct, run `python3 changelog.py --output CHANGELOG.md`.
3. Show the user the generated file and offer to commit it.

## Options

- `--since <ref>` — start from a specific tag or commit instead of the latest tag
- `--version <semver>` — override detected version from package manifests
- `--dry-run` — print to stdout without writing

## Categories

Commits are bucketed into Added, Fixed, Changed, Removed, and Security using
conventional-commit prefixes and common natural-language keywords. Breaking
changes are highlighted in a dedicated section.
