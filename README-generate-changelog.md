# Generate Changelog Skill

A small Claude Code-friendly utility that creates a structured `CHANGELOG.md` from git history.

## Setup in 3 steps

1. Copy `changelog.sh` into the root of any git repository.
2. Run `chmod +x changelog.sh`.
3. Run `bash changelog.sh` to write `CHANGELOG.md`.

## What it does

- Fetches tags and finds the latest tag with `git describe --tags --abbrev=0`.
- Reads commits from the latest tag to `HEAD` (or all history when no tag exists).
- Categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Keep a Changelog style `CHANGELOG.md`.

## Optional output path

```bash
bash changelog.sh docs/CHANGELOG.md
```

## Claude Code usage

Ask Claude Code:

```text
/generate-changelog
Run bash changelog.sh, inspect the generated CHANGELOG.md, and adjust wording only if needed.
```

## Categorization rules

- `feat:`, `feature:`, `add:` → `Added`
- `fix:`, `bugfix:`, `hotfix:` → `Fixed`
- `remove:`, `delete:` → `Removed`
- `refactor:`, `perf:`, `docs:`, `style:`, `test:`, `ci:`, `chore:`, `update:` → `Changed`
- Anything else defaults to `Changed`
