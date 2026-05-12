# Generate Changelog From Git History

This script creates a structured `CHANGELOG.md` from commit subjects since the last git tag. If the repository has no tags, it uses the full available history.

## Setup

1. Copy `tools/generate-changelog/changelog.sh` into your repository.
2. Run `bash tools/generate-changelog/changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Categories

- `Added`: commits starting with `feat`, `add`, `added`, or `create`.
- `Fixed`: commits starting with `fix`, `bug`, `bugfix`, `patch`, or `hotfix`.
- `Changed`: all other commits.
- `Removed`: commits starting with `remove`, `removed`, `delete`, or `drop`.

## Options

```bash
bash tools/generate-changelog/changelog.sh --repo . --output CHANGELOG.md
bash tools/generate-changelog/changelog.sh --from v1.2.0 --version v1.3.0
```

The output is deterministic for the current git history and includes short commit hashes so reviewers can trace each entry.
