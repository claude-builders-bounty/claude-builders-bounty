# generate-changelog

Claude Code skill + bash script that builds a structured `CHANGELOG.md` from git history since the last tag.

Bounty target: [claude-builders-bounty#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1) ($50).

## Setup (3 steps)

1. Copy `skills/generate-changelog/` into your Claude Code skills folder (or keep this repo nearby).
2. Make the script executable: `chmod +x changelog.sh`
3. From any git repo: `bash /path/to/changelog.sh`

Optional: invoke via `/generate-changelog` once the skill is installed.

## What it does

- Reads commits since the latest git tag (or all commits if untagged)
- Sorts subjects into **Added / Fixed / Changed / Removed**
- Writes `CHANGELOG.md`

## Samples

- `samples/CHANGELOG.sample.md` — script output on a tagged history
- `samples/CHANGELOG.is-docker.md` — categorized commits from [sindresorhus/is-docker](https://github.com/sindresorhus/is-docker) around `v4.0.0`
