# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup in 3 Steps

1. Copy `skills/generate-changelog/` into your project or run it from this repository.
2. From the target repository root, run `bash skills/generate-changelog/changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Behavior

- Finds the latest git tag with `git describe --tags --abbrev=0`.
- If no tag exists, reads all commits reachable from `HEAD`.
- Categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown changelog with commit hashes for traceability.

## Classification Rules

- `Added`: `feat`, `feature`, `add`, `create`, `implement`
- `Fixed`: `fix`, `bugfix`, `repair`, `hotfix`
- `Removed`: `remove`, `delete`, `drop`, `deprecate`
- `Changed`: everything else, including `chore`, `docs`, `refactor`, and uncategorized commits

## Example

See `examples/sample-output.md` for output generated against this repository.

On systems without Bash, run the same implementation directly:

```bash
python3 skills/generate-changelog/changelog.py
```
