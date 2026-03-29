# Generate Changelog (Bounty #1)

A Bash script and Claude Code `SKILL.md` that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Acceptance Criteria Met
- ✅ Works via `bash changelog.sh` (or Claude Code can read `SKILL.md` to run it when asked)
- ✅ Fetches commits since the last git tag (or since initial commit if no tags)
- ✅ Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- ✅ Outputs a properly formatted `CHANGELOG.md`
- ✅ Includes a sample output

## Installation

**Option 1: As a Claude Code Skill**
Save `SKILL.md` and `changelog.sh` into your `.claude/skills/changelog` directory.

**Option 2: Direct Bash Script**
Copy the `changelog.sh` into your project root and run it:
```bash
chmod +x changelog.sh
./changelog.sh
```

## Sample Output

See `CHANGELOG_SAMPLE.md` for output generated from this repository.
