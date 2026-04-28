# Generate Changelog Skill

Automatically generates a structured `CHANGELOG.md` from git history.

## Setup (3 steps or fewer)

1. Copy `changelog.sh` into your project (or reference it from this repo)
2. Run from your project root: `bash changelog.sh`
3. Review the generated `CHANGELOG.md`

## Usage with Claude Code

Add this skill to your project's `.claude/skills/` directory or reference the SKILL.md. Then use:

```
/generate-changelog
```

## How it works

1. Finds the most recent git tag
2. Collects all commits since that tag
3. Auto-categorizes by commit prefix:
   - `feat:`, `add:` → Added
   - `fix:`, `bugfix:` → Fixed
   - `refactor:`, `change:`, `update:` → Changed
   - `remove:`, `delete:` → Removed
4. Prepends the entry to `CHANGELOG.md`

## Requirements

- Git
- Standard Unix tools (date, sed, grep) — no additional dependencies
