# Generate Changelog

A small Bash utility that creates a structured `CHANGELOG.md` from git history.
It finds the latest git tag, reads commits from that tag to `HEAD`, and groups
commit subjects into `Added`, `Fixed`, `Changed`, and `Removed` sections.

## Setup

1. Copy `changelog.sh` into any git repository.
2. Run `bash changelog.sh` from the repository root.
3. Review the generated `CHANGELOG.md` and commit it.

## Usage

```bash
bash tools/generate-changelog/changelog.sh
```

Write to a custom path:

```bash
bash tools/generate-changelog/changelog.sh docs/CHANGELOG.md
```

## How It Works

- If the repository has tags, commits are collected from the latest tag to
  `HEAD`.
- If no tags exist, the script uses the full reachable history.
- Conventional commit prefixes and common verbs drive categorization:
  - `Added`: `feat`, `add`, `create`, `implement`, `initial`
  - `Fixed`: `fix`, `bugfix`, `resolve`, `repair`, `correct`
  - `Changed`: `docs`, `chore`, `refactor`, `test`, `update`, `improve`
  - `Removed`: `remove`, `delete`, `drop`, `deprecate`
- Unmatched commits fall back to `Changed` so nothing is lost.

See `sample-output.md` for output generated from this repository.
