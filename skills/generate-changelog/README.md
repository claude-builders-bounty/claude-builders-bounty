# 📋 generate-changelog — Claude Code Skill

Auto-generate a structured `CHANGELOG.md` from your project's git history — zero dependencies, works in any repo.

## Setup (3 steps)

```bash
# 1. Copy the files into your project
cp generate-changelog.sh .claude/skills/
cp SKILL.md .claude/skills/generate-changelog.md

# 2. Make the script executable
chmod +x .claude/skills/generate-changelog.sh

# 3. Use it
```

Then in Claude Code, just type `/generate-changelog`.

## What you get

- Commits since your last git tag (or full history if no tags)
- Auto-categorised into Added / Fixed / Changed / Removed / Other
- Keep a Changelog–compliant Markdown output
- Diff link at the bottom (when a GitHub remote is detected)

See `sample-CHANGELOG.md` for example output.

## Conventional commit prefixes recognised

| Section | Prefixes |
|---|---|
| ✨ Added | `feat:`, `add:`, `new:`, `feature:` |
| 🐛 Fixed | `fix:`, `bug:`, `hotfix:`, `patch:`, `resolve:` |
| 🔧 Changed | `refactor:`, `chore:`, `perf:`, `docs:`, `style:`, `ci:`, `build:`, `test:`, `bump:`, `update:`, `improve:`, `upgrade:` |
| 🗑️ Removed | `remove:`, `delete:`, `drop:`, `deprecate:` |
| 📝 Other | everything else |

## Direct usage

```bash
bash generate-changelog.sh              # writes CHANGELOG.md
bash generate-changelog.sh CHANGES.md  # custom output file
```
