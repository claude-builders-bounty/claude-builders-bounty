# Generate Changelog

Generate a structured `CHANGELOG.md` from git history since the latest tag.

## Setup

1. Copy `changelog.sh` into any git repository.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Usage

```bash
bash changelog.sh
```

To write to a custom path:

```bash
bash changelog.sh docs/CHANGELOG.md
```

The script detects the latest git tag with `git describe --tags --abbrev=0`.
If the repository has no tags, it uses the full commit history.

## Categories

- `Added`: `feat`, `feature`, `add`.
- `Fixed`: `fix`, `bug`, `hotfix`.
- `Removed`: `remove`, `removed`, `delete`, `deleted`.
- `Changed`: everything else, including `refactor`, `chore`, `docs`, `test`,
  `ci`, and uncategorized commits.

## Claude Code Command

Use the included `SKILL.md` as the backing skill for `/generate-changelog`.
The skill delegates generation to the same script so manual and Claude-driven
usage produce identical output.
