# Generate Changelog (Claude Code skill)

Structured `CHANGELOG.md` from git commits since the latest tag.

## Setup (3 steps)

1. Copy this folder to `.claude/skills/generate-changelog/` in your project (include `changelog.sh` and `SKILL.md`).
2. Ensure `changelog.sh` is executable: `chmod +x .claude/skills/generate-changelog/changelog.sh`.
3. In Claude Code, run **`/generate-changelog`**, or from any repo: `bash path/to/changelog.sh`.

## Manual usage

```bash
# Write ./CHANGELOG.md in the current repo
bash changelog.sh

# Another repository
bash changelog.sh /path/to/repo

# Preview on stdout
bash changelog.sh -f .
```

## Categories

| Section   | Conventional commits / keywords                          |
|-----------|----------------------------------------------------------|
| Added     | `feat:`, `add`, `new`, …                                 |
| Fixed     | `fix:`, `bugfix`, `hotfix`, …                            |
| Changed   | `chore:`, `refactor:`, `update`, … (default if unclear)  |
| Removed   | `remove:`, `delete:`, `drop`, …                          |

## Files

- `changelog.sh` — portable Bash generator
- `SKILL.md` — Claude Code `/generate-changelog` skill
- `samples/` — example output from real repositories
