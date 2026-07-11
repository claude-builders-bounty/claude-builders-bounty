---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag (Added/Fixed/Changed/Removed).
---

# Generate Changelog

## When to use

User asks for a changelog, release notes, or runs `/generate-changelog`.

## Steps

1. Confirm you are inside a git repository root.
2. Run the helper script from this skill directory (or the copy checked into the project):

```bash
bash path/to/bounties/01-generate-changelog/changelog.sh CHANGELOG.md
```

3. Show the user the generated file path and a short summary of section counts.
4. If there is no git tag, the script uses full `HEAD` history and notes that in the header.

## Categories

| Section | Heuristics |
|---------|------------|
| Added | `feat:`, add/implement/introduce |
| Fixed | `fix:`, fix/bugfix/hotfix/patch |
| Changed | `chore`/`refactor`/`docs`/update/improve, plus unmatched subjects |
| Removed | remove/delete/drop/`revert` |

## Notes

- Prefer not to invent commits; only use `git log` subjects.
- Leave existing `CHANGELOG.md` history alone unless the user asks to merge manually.
