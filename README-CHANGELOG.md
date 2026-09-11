# generate-changelog (Opire bounty)

## Setup (3 steps)
1. Copy `scripts/changelog.sh` into your repo (and optionally `skills/generate-changelog/SKILL.md` for Claude Code).
2. `chmod +x scripts/changelog.sh`
3. Run `bash scripts/changelog.sh` — writes/updates `CHANGELOG.md` from commits since the last git tag.

## Options
- `bash scripts/changelog.sh --stdout-only`
- `SINCE_REF=v1.2.0 bash scripts/changelog.sh`
- `REPO_DIR=/path/to/repo OUT_FILE=CHANGELOG.md bash scripts/changelog.sh`

## Categories
Commits are auto-sorted into **Added / Fixed / Changed / Removed** from conventional message keywords (`feat`, `fix`, `remove`, `chore`, …).

## Sample
See `samples/CHANGELOG.sample.md` (generated on this repository).
