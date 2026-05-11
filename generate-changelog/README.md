# Generate Changelog

Generate a structured `CHANGELOG.md` from git history.

## Setup

1. Copy `generate-changelog/changelog.sh` into the repository you want to document.
2. Run `bash changelog.sh` from that repository root.
3. Review and commit the generated `CHANGELOG.md`.

## Usage

```bash
bash generate-changelog/changelog.sh
```

```bash
bash generate-changelog/changelog.sh --since v1.2.3 --version 1.3.0 --output CHANGELOG.md
```

## What It Does

- Fetches tags from `origin` when available.
- Finds commits since the latest reachable git tag.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Keep a Changelog-style `CHANGELOG.md`.

## Options

| Option | Description |
| --- | --- |
| `--since <tag>` | Use a specific starting tag instead of the latest tag. |
| `--version <name>` | Set the changelog heading. Defaults to `Unreleased`. |
| `--output <file>` | Set the output path. Defaults to `CHANGELOG.md`. |
| `--repo <path>` | Generate a changelog for a different local repository. |
| `--no-fetch` | Skip `git fetch --tags`. |
| `--help` | Print command help. |
