# generate-changelog

Structured `CHANGELOG.md` from git history since the last tag.

## Setup (3 steps)

1. Copy `changelog.sh` into your repo (or keep this folder on your `PATH`).
2. Make it executable: `chmod +x changelog.sh`
3. Run: `./changelog.sh` → writes `CHANGELOG.md`

Optional Claude Code skill: copy `skills/generate-changelog/` into your skills directory; invoke as `/generate-changelog`.

## Categories
Commits are auto-sorted into **Added / Fixed / Changed / Removed** using conventional-commit prefixes and common English verbs.

## Sample
See `samples/CHANGELOG.sample.md` generated from this repository.
