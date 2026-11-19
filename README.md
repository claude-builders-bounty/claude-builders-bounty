# Generate a structured CHANGELOG

Status: ready-to-ship for review.

Use the command `/generate-changelog` or `bash changelog.sh` to build a `CHANGELOG.md` from the project's git history.

## What it does

1. Finds the most recent git tag with `git describe --tags --abbrev=0`.
2. Collects commits since that tag with `git log <tag>..HEAD` (no merges).
3. Buckets subjects into Added / Fixed / Changed / Removed based on Conventional Commits prefixes (`feat`, `fix`, `remove`, `revert`, etc.).
4. Writes a `CHANGELOG.md` at the repo root.

## How it worked on a real repo

Tested on `WangJiaQi032/ThirdWorldDomination` — see `tests/sample-output.md` for an example run.

## Install (3 steps)

1. Copy `changelog.sh` into your repo root and `chmod +x changelog.sh`.
2. Add the Claude skill `skills/changelog/SKILL.md` or invoke `/generate-changelog`.
3. Run once: `bash changelog.sh`.

## Files

| File | Purpose |
|---|---|
| `changelog.sh` | Bash generator (no external dependencies) |
| `skills/changelog/SKILL.md` | Claude Code skill for `/generate-changelog` |
| `tests/sample-output.md` | Output produced from a public repo |
