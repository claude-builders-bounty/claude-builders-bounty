# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from git history since the latest tag.

## Setup and Usage

1. Copy this repository's `changelog.sh` and `skills/generate-changelog/` directory into your project root.
2. Run `bash changelog.sh` from the project root.
3. Review the generated `CHANGELOG.md`, then commit it with your release changes.

## Options

```bash
bash changelog.sh --repo /path/to/repo
bash changelog.sh --since v1.2.3 --output RELEASE_NOTES.md
```

The generator uses the latest reachable git tag by default. If no tag exists, it includes the full history. Commit subjects are categorized as:

- `Added`: feature and add-style commits
- `Fixed`: bug fix commits
- `Changed`: refactors, chores, docs, tests, builds, CI, and uncategorized work
- `Removed`: remove, delete, drop, and deprecation commits

See `samples/CHANGELOG.sample.md` for output captured from a real GitHub repository.
