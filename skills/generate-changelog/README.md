# generate-changelog

Structured `CHANGELOG.md` generator for the claude-builders-bounty issue #1 deliverable.

## Setup (3 steps)

1. Copy `changelog.py` and `SKILL.md` into your project (or clone this folder).
2. `cd` into any git repository and run `python3 changelog.py --dry-run`.
3. Write the file: `python3 changelog.py --output CHANGELOG.md`.

Requires Python 3.10+ and git. No third-party packages.

## Claude Code

Place `SKILL.md` in `.claude/skills/generate-changelog/` then invoke `/generate-changelog`.
