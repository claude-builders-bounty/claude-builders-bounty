# changelog-skill

Generate a structured `CHANGELOG.md` from git history in 3 steps.

## Setup (3 steps or fewer)
1. Copy `changelog.sh` (and optionally `SKILL.md`) into your project.
2. Run `bash changelog.sh` from the repo root.
3. Commit the generated `CHANGELOG.md`.

## What it does
- Fetches commits **since the last git tag** (falls back to full history if untagged).
- Auto-categorizes conventional-commit subjects into **Added / Fixed / Changed / Removed**.
- Writes a properly formatted `CHANGELOG.md` with a dated version heading.

## Options
- `-o FILE` — write to a custom path (default `CHANGELOG.md`).
- `--all` — ignore tags and use full history.

See `sample-CHANGELOG.md` for example output, and `SKILL.md` to use it as a
Claude Code skill (`/generate-changelog`).
