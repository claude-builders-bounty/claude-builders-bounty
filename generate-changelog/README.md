# Generate Changelog

Structured `CHANGELOG.md` generator for Claude Code projects.

## Setup (2 steps)

**Step 1:** Copy the `generate-changelog/` folder into your repo (or install the skill globally under `~/.cursor/skills/generate-changelog/`).

**Step 2:** Run:

```bash
bash generate-changelog/changelog.sh
```

## What you get

- Commits since the latest git tag (or full history if no tags)
- Sections: `Added`, `Fixed`, `Changed`, `Removed`
- Conventional-commit aware categorization with keyword fallback
- Output written to `CHANGELOG.md`

## Sample output

See `samples/CHANGELOG-sample.md`, generated from this repository's git history during validation.

## Skill usage

In Claude Code/Cursor, invoke **`/generate-changelog`** after installing `SKILL.md` as a skill (see `SKILL.md` frontmatter `name: generate-changelog`).

## Acceptance criteria (bounty #1)

- [x] `/generate-changelog` skill or `bash changelog.sh`
- [x] Commits since last git tag
- [x] Sections: Added / Fixed / Changed / Removed
- [x] Writes `CHANGELOG.md`
- [x] Sample output: `samples/CHANGELOG-sample.md`

Closes claude-builders-bounty/claude-builders-bounty#1
