# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup

1. Copy this folder into the target repository.
2. Run `bash skills/generate-changelog/changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## What It Does

- Finds the latest git tag and reads commits after that tag.
- Falls back to the full history when the repository has no tags.
- Ignores merge commits.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown changelog at the repository root.

## Categorization

The script looks at each commit subject:

- `Added`: `feat`, `add`, `create`, `implement`, `introduce`, `init`
- `Fixed`: `fix`, `bug`, `patch`, `repair`, `resolve`, `correct`
- `Removed`: `remove`, `delete`, `drop`, `deprecate`
- `Changed`: everything else, including `refactor`, `docs`, `test`, `chore`, and `update`

## Example

```bash
bash skills/generate-changelog/changelog.sh
```

```text
Generated CHANGELOG.md from 7 commits.
Range: v1.2.0..HEAD
```

See `sample-output.md` for output captured from a real tagged git repository.
