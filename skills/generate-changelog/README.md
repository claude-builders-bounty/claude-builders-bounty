# /generate-changelog Skill

A Claude Code skill that auto-generates a structured `CHANGELOG.md` from your git history.

## Install (3 steps)

**Step 1:** Copy the files:
```bash
mkdir -p ~/.claude/skills
cp SKILL.md ~/.claude/skills/generate-changelog.md
cp changelog.sh ~/.claude/skills/changelog.sh
chmod +x ~/.claude/skills/changelog.sh
```

**Step 2:** Register the skill in `~/.claude/settings.json`:
```json
{
  "skills": [
    { "name": "generate-changelog", "path": "~/.claude/skills/generate-changelog.md" }
  ]
}
```

**Step 3:** Run it in any git project:
```
/generate-changelog
```

## Features

- Fetches commits **since the last git tag** (or all commits if no tags exist)
- Auto-categorizes commits into `Added` / `Fixed` / `Changed` / `Removed`
  - Understands [Conventional Commits](https://www.conventionalcommits.org/) prefixes (`feat:`, `fix:`, `chore:`, etc.)
  - Falls back to keyword matching for non-conventional messages
- Outputs a [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) formatted `CHANGELOG.md`
- Preserves existing changelog entries below the new section
- Works via `/generate-changelog` in Claude Code or directly as `bash changelog.sh`

## Requirements

- bash 4+
- git
- Claude Code with skills support
