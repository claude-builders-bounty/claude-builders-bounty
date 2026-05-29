# Generate Changelog

Use this skill when a user asks Claude Code to create or refresh a Markdown changelog from the current repository's git history.

## What it does

- Finds the latest reachable git tag with `git describe --tags --abbrev=0`.
- Reads non-merge commits from that tag through `HEAD`.
- Categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a concise Markdown changelog.

## Usage

From the repository root:

```bash
./skills/generate-changelog/changelog.sh [output-file] [version]
```

Examples:

```bash
./skills/generate-changelog/changelog.sh
./skills/generate-changelog/changelog.sh CHANGELOG.md v1.2.0
./skills/generate-changelog/changelog.sh docs/CHANGELOG.md "2026-05-29"
```

## Classification

The generator recognizes conventional commit prefixes such as `feat:`, `fix:`, `docs:`, `refactor:`, and `remove:`. Unknown prefixes and plain commit subjects are placed in `Changed`.

## Verification

Run:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
