# Generate Changelog Skill

The `skills/generate-changelog` skill creates a structured `CHANGELOG.md` from git history.

## Usage

```bash
python skills/generate-changelog/scripts/generate_changelog.py
```

Optional arguments:

```bash
python skills/generate-changelog/scripts/generate_changelog.py --output CHANGELOG.md
python skills/generate-changelog/scripts/generate_changelog.py --from v1.2.0 --to HEAD
python skills/generate-changelog/scripts/generate_changelog.py --dry-run
```

## Behavior

- Uses the latest reachable git tag as the starting point.
- Falls back to the full history when no tag exists.
- Groups commits into Added, Changed, Fixed, Removed, Security, Deprecated, and Other.
- Prepends the generated section to an existing changelog.
- Keeps uncategorized commits in Other for manual review.

## Review Notes

Automated categorization is intentionally conservative. Review the generated `Other` section before publishing a release.
