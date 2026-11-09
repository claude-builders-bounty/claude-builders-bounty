# generate-changelog (Opire bounty)

Bash + Claude Code skill that builds a structured `CHANGELOG.md` from git history.

## Setup (3 steps)
1. Copy `changelog.sh` into your repo root (or keep this folder on `PATH`).
2. Optional: copy `skills/generate-changelog/` into your Claude Code skills directory.
3. Run `bash changelog.sh` (or `/generate-changelog`).

## Acceptance
- Commits since last tag are categorized into Added / Fixed / Changed / Removed
- Writes `CHANGELOG.md`
- Sample output included under `sample-output/CHANGELOG.md`
