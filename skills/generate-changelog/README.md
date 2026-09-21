# generate-changelog

Structured `CHANGELOG.md` from git history since the last tag. Bash **or** Claude Code skill.

## Setup (3 steps)

1. Copy `skills/generate-changelog/` (and optional root `changelog.sh`) into your repo.
2. From the repo root run: `bash changelog.sh` **or** `python3 skills/generate-changelog/scripts/changelog.py`
3. Commit the generated `CHANGELOG.md` (sample from a real repo: `examples/sample-CHANGELOG.md`).

Requires: `git` + `python3` (stdlib only).

## Acceptance map (bounty #1)

| Criterion | How |
|-----------|-----|
| `/generate-changelog` or `bash changelog.sh` | `SKILL.md` + `changelog.sh` |
| Commits since last tag | `git describe --tags --abbrev=0` then `git log TAG..HEAD` |
| Added / Fixed / Changed / Removed | Conventional + keyword rules |
| Formatted CHANGELOG.md | Keep-a-Changelog sections |
| Tested on real GitHub repo | `examples/sample-CHANGELOG.md` from [expressjs/express](https://github.com/expressjs/express) since `v5.2.1` |
| README ≤ 3 setup steps | This file |

## Slash command

In Claude Code, install the skill folder so `/generate-changelog` loads `SKILL.md` and runs the script above.
