# generate-changelog

Generate structured `CHANGELOG.md` from git history.

## Trigger

When user says:
- "generate changelog"
- "/generate-changelog"
- "create CHANGELOG"
- "update changelog"

## Steps

1. Check if `changelog.py` exists in project root
   - If not, copy from this skill directory
2. Run `python3 changelog.py`
3. Review generated `CHANGELOG.md`
4. Commit the changelog

## Output Format

Keep a Changelog format:
- `### Added` — feat:, add:, feature:
- `### Fixed` — fix:, bug:, hotfix:
- `### Changed` — refactor:, chore:, update:, change:
- `### Removed` — remove:, delete:, drop:
- `### Other` — docs:, test:, style:, ci:, build:

## Configuration

Optional `.changelog.yml` for custom category mappings.
