# Generate Changelog

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy `generate-changelog/changelog.sh` into any git repository.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Claude Code Skill

Copy `generate-changelog/SKILL.md` into a Claude Code skill folder and invoke it as `/generate-changelog`.

## Output Categories

The script maps commit subjects into:

- `Added`: `feat:`, `feature:`, `add:`, or matching add/create/implement keywords.
- `Fixed`: `fix:`, `bugfix:`, or matching fix/repair/bug keywords.
- `Changed`: `refactor:`, `chore:`, `docs:`, `perf:`, `test:`, `build:`, `ci:`, or uncategorized commits.
- `Removed`: `remove:`, `delete:`, or matching remove/delete keywords.

## Example

```bash
bash generate-changelog/changelog.sh --repo . --output CHANGELOG.md
```
