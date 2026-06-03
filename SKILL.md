# Generate Changelog

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from git history.

## Usage

```bash
# Via bash
bash changelog.sh

# Or as a Claude Code skill (after installing):
/generate-changelog
```

## Installation

```bash
# Copy the skill to your project
cp SKILL.md .claude/skills/generate-changelog/SKILL.md
cp changelog.sh .claude/skills/generate-changelog/changelog.sh
```

## What It Does

1. Fetches commits since the last git tag (or the first 50 commits if no tags exist)
2. Auto-categorizes commits into: **Added** / **Fixed** / **Changed** / **Removed**
3. Groups by semantic type using conventional commit prefixes
4. Outputs a clean, ready-to-use `CHANGELOG.md`

## Acceptance Criteria

- Works via `/generate-changelog` command or `bash changelog.sh`
- Fetches commits since the last git tag
- Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- Outputs a properly formatted `CHANGELOG.md`
- Tested on a real GitHub repo (see sample output below)
- README with setup instructions in 3 steps or fewer
