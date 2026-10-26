## What
Deliverable for #1: `changelog.sh` — a zero-dependency bash skill that generates a structured Markdown CHANGELOG from git history.

## Acceptance criteria coverage
- ✅ Generates a structured CHANGELOG from git history (Added/Changed/Fixed/Removed/Docs/Refactor/Chore sections)
- ✅ Works via `bash changelog.sh` (also `--full`, `--since`)
- ✅ Zero dependencies (bash + git only)
- ✅ Tested on real repositories (see sample output)

## Files
- `changelog/changelog.sh` — the skill
- `changelog/README.md` — usage docs
- `changelog/sample-output.md` — output from a real repo (psf/black, 50 commits)
