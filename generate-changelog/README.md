# Generate Changelog

A small Bash tool that turns git history into a structured `CHANGELOG.md`.

## Setup in 3 steps

1. Copy `generate-changelog/changelog.sh` into any git repository.
2. Run `bash changelog.sh` from the repository root.
3. Review the generated `CHANGELOG.md` and commit it.

## What it does

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Reads commits since that tag, or all commits when no tag exists.
- Categorizes commit messages into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a clean Markdown changelog with commit hash and author included.

## Supported command

```bash
bash generate-changelog/changelog.sh
```

You can also choose a custom output file:

```bash
bash generate-changelog/changelog.sh RELEASE_NOTES.md
```

## Categorization rules

- `feat:`, `add:`, `create:`, `implement:` → `Added`
- `fix:`, `bugfix:`, `hotfix:`, `resolve:` → `Fixed`
- `remove:`, `delete:`, `drop:`, `deprecate:` → `Removed`
- `docs:`, `refactor:`, `test:`, `chore:`, `ci:`, `build:`, other updates → `Changed`

Commits that do not match a known prefix go into `Changed` so nothing is lost.

## Test result

Tested on the public `claude-builders-bounty/claude-builders-bounty` repository and on a local git repo with tagged history. A sample output is included in `samples/sample-changelog.md`.
